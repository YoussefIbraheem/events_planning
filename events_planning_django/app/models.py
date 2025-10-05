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

    class EventType(models.TextChoices):
        SEATED = "seated", "Seated"
        GENERAL_ADMISSION = "general_admission", "General Admission"

    title = models.CharField(max_length=255)
    description = models.TextField(max_length=1000)
    coordinates = models.JSONField(
        default=dict, validators=[validate_coordinates]
    )  # {'lat': xx.xxxx, 'lng': yy.yyyy}
    location_type = models.CharField(
        max_length=100, choices=EventType.choices
    )  # e.g., 'indoor', 'outdoor'
    date_time = models.DateTimeField()
    tickets_available = models.PositiveIntegerField()
    ticket_price = models.FloatField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    organiser = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="events",
        validators=[validate_user_is_organiser],
    )


class Ticket(models.Model):

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="tickets")

    ticket_code = models.CharField(max_length=255, unique=True)
    seat_number = models.CharField(max_length=255, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    attendee = models.ForeignKey(CustomUser, null=True, on_delete=models.DO_NOTHING,validators=[validate_user_is_attendee], related_name="tickets")
