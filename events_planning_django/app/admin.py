from django.contrib import admin
from app.models import CustomUser, Ticket, Order, Event, OrderItem
from .forms import UserForm


class UserAdmin(admin.ModelAdmin):
    model = CustomUser
    form = UserForm
    list_display = ["username", "email", "user_type"]
    fieldsets = [
        (
            None,
            {
                "fields": ["username"],
            },
        ),
        (
            None,
            {
                "fields": ["email"],
            },
        ),
        ("Password Fields", {"fields": [("password", "confirm_password")]}),
        (
            "Name",
            {
                "fields": [("first_name", "last_name")],
            },
        ),
    ]


class EventAdmin(admin.ModelAdmin):
    model = Event
    list_display = ["title", "date_time", "tickets_amount", "ticket_price"]
    fieldsets = (
        (
            None,
            {
                "fields": ["title"],
            },
        ),
        (
            None,
            {
                "fields": ["description"],
            },
        ),
        (
            "Tickets Data",
            {
                "fields": ["tickets_amount", "ticket_price"],
            },
        ),
        (
            "Logistics",
            {
                "fields": ["date_time"],
            },
        ),
        (
            "Coordinates",
            {
                "fields": [("latitude", "longitude")],
            },
        ),
        (
            "Organiser",
            {
                "fields": ["organiser"],
            },
        ),
    )


admin.site.register(CustomUser, UserAdmin)
admin.site.register(Event, EventAdmin)
