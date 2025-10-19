from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class CustomUser(AbstractUser):

    class UserType(models.TextChoices):
        ATTENDEE = "attendee", "Attendee"
        ORGANISER = "organiser", "Organiser"

    user_type = models.CharField(
        max_length=20, choices=UserType.choices, default=UserType.ATTENDEE
    )

    def is_attendee(self):
        return self.user_type == self.UserType.ATTENDEE

    def is_organiser(self):
        return self.user_type == self.UserType.ORGANISER


def validate_user_is_organiser(user):
    if user.user_type != CustomUser.UserType.ORGANISER:
        raise ValidationError("User must be an organiser.")


def validate_user_is_attendee(user):
    if user.user_type != CustomUser.UserType.ATTENDEE:
        raise ValidationError("User must be an attendee.")


def validate_coordinates(value):
    if not isinstance(value, dict):
        raise ValidationError(
            "Coordinates must be a dictionary with 'lat' and 'lng' keys."
        )
    if "lat" not in value or "lng" not in value:
        raise ValidationError("Coordinates must include 'lat' and 'lng' keys.")
    lat = value["lat"]
    lng = value["lng"]
    if not (-90 <= lat <= 90):
        raise ValidationError("Latitude must be between -90 and 90.")
    if not (-180 <= lng <= 180):
        raise ValidationError("Longitude must be between -180 and 180.")


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
    latitude = models.DecimalField(max_digits=9, decimal_places=6,default=0.00)
    longitude = models.DecimalField(max_digits=9, decimal_places=6,default=0.00)
    date_time = models.DateTimeField()
    event_status = models.CharField(choices=Status.choices , default= Status.SOON)
    tickets_amount = models.PositiveIntegerField()
    ticket_price = models.FloatField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    organiser = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="events",
    )


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

    
