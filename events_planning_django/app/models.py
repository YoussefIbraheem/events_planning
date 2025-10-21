from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import timezone
from django.contrib.auth.models import UserManager


class SoftDeleteQureySet(models.QuerySet):  # Custom QuerySet to handle soft deletion

    def delete(self):
        """Soft deletes the records by setting the deleted_at field to now.

        Returns:
            int: Number of records soft deleted
        """
        return super().update(deleted_at=timezone.now())

    def hard_delete(self):
        """Permanently deletes the records from the database.
        Returns:
            int: Number of records permanently deleted
        """
        return super().delete()

    def alive(self):
        """Returns a queryset of all alive (not soft-deleted) records.
        Returns:
            QuerySet: QuerySet of alive records
        """
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        """Returns a queryset of all soft-deleted records.
        Returns:
            QuerySet: QuerySet of soft-deleted records
        """
        return self.exclude(deleted_at__isnull=True)


class CustomUserManager(
    UserManager
):  # Custom manager to handle soft deletion by overriding the original UserManager

    def get_queryset(self):
        return SoftDeleteQureySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        """Returns a queryset of all users, including soft-deleted ones.

        Returns:
            QuerySet: QuerySet of all users
        """
        return SoftDeleteQureySet(self.model, using=self._db)

    def deleted_only(self):
        """Returns a queryset of only soft-deleted users.
        Returns:
            QuerySet: QuerySet of soft-deleted users
        """
        return SoftDeleteQureySet(self.model, using=self._db).dead()


class CustomUser(AbstractUser):

    class UserType(models.TextChoices):
        ATTENDEE = "attendee", "Attendee"
        ORGANISER = "organiser", "Organiser"

    user_type = models.CharField(
        max_length=20, choices=UserType.choices, default=UserType.ATTENDEE
    )

    deleted_at = models.DateTimeField(blank=True, null=True)

    objects = CustomUserManager()

    def is_attendee(self):
        """verifies if the user is an attendee

        Returns:
            bool: True if the user is an attendee, False otherwise
        """
        return self.user_type == self.UserType.ATTENDEE

    def is_organiser(self):
        """verifies if the user is an organiser
        Returns:
            bool: True if the user is an organiser, False otherwise
        """
        return self.user_type == self.UserType.ORGANISER

    def soft_delete(self):
        """Soft deletes the user by setting the deleted_at field to now."""
        self.deleted_at = timezone.now()
        self.save(update_fields=["deleted_at"])

    def restore(self):
        """Restores a soft-deleted user by clearing the deleted_at field."""
        self.deleted_at = None
        self.save(update_fields=["deleted_at"])


def validate_user_is_organiser(user):
    if user.user_type != CustomUser.UserType.ORGANISER:
        raise ValidationError("User must be an organiser.")


def validate_user_is_attendee(user):
    if user.user_type != CustomUser.UserType.ATTENDEE:
        raise ValidationError("User must be an attendee.")


class Event(models.Model):

    class Status(models.TextChoices):
        SOON = "soon", "Soon"
        UPCOMING = "upcoming", "Upcoming"
        WITHHELD = "withheld", "Withheld"
        POSTPONED = "postponed", "Postponed"
        ONGOING = "ongoing", "Ongoing"
        CANCELLED = "cancelled", "Cancelled"
        FINISHED = "finished", "Finished"

    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, default=0.00)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, default=0.00)
    date_time = models.DateTimeField()
    event_status = models.CharField(choices=Status.choices, default=Status.SOON)
    tickets_amount = models.PositiveIntegerField()
    ticket_price = models.FloatField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    organiser = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="events",
    )

    def __str__(self):
        return self.title


class Order(models.Model):
    class PaymentMethod(models.TextChoices):
        CASH = "cash", "Cash"
        CREDIT = "credit", "Credit"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"  # created but not reserved
        RESERVED = "reserved", "Reserved"  # tickets reserved / held
        PAID = "paid", "Paid"  # finalized & sold
        CANCELLED = "cancelled", "Cancelled"  # cancelled by user or system
        EXPIRED = "expired", "Expired"

    total_price = models.FloatField(max_length=10, default=0)
    payment_method = models.CharField(max_length=255, choices=PaymentMethod.choices)
    order_status = models.CharField(
        max_length=255, choices=Status.choices, default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    attendee = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="orders"
    )


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    ticket_price = models.FloatField(max_length=10)
    quantity = models.PositiveIntegerField(default=1)


class Ticket(models.Model):

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")

    ticket_code = models.CharField(max_length=255, unique=True)
    attendee = models.ForeignKey(
        CustomUser,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets",
    )
    order_item = models.ForeignKey(
        "OrderItem",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="tickets",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    reserved_until = models.DateTimeField(null=True, blank=True)
