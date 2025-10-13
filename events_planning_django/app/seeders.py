from .factories import (
    UserFactory,
    EventFactory,
    TicketFactory,
    OrderFactory,
    OrderItemFactory,
)
from .models import CustomUser, Event, Ticket, Order, OrderItem
from abc import ABC, abstractmethod
from django.db.models import Q, Count, F
from django.db import IntegrityError, transaction
import random


class AbstractSeeder(ABC):

    @abstractmethod
    def seed(self, *args, **kwargs):
        pass


class UserSeeder(AbstractSeeder):

    def seed(self, *args, **kwargs):
        factory = UserFactory()
        count = kwargs.get("count")
        user_type = kwargs.get("user_type")
        if user_type not in ["attendee", "organiser"]:
            raise ValueError("user_type must be either 'attendee' or 'organiser'")
        for _ in range(count):
            user_data = factory.create(user_type=user_type)
            user = CustomUser.objects.create_user(**user_data)
            user.save()
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} users"))


class EventSeeder(AbstractSeeder):

    def seed(self, *args, **kwargs):
        factory = EventFactory()
        count = kwargs.get("count")
        events_created = 0
        for _ in range(count):
            user = (
                CustomUser.objects.filter(user_type=CustomUser.UserType.ORGANISER)
                .order_by("?")
                .first()
            )
            if not user:
                self.stdout.write(
                    self.style.ERROR(
                        "No organiser users found. Please seed organiser users first."
                    )
                )
                return
            event_data = factory.create(organiser=user)
            event = Event.objects.create(**event_data)
            event.save()
            events_created += 1
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {events_created} events"))


class TicketSeeder(AbstractSeeder):

    def seed(self, *args, **kwargs):
        factory = TicketFactory()
        count = kwargs.get("count")
        for _ in range(count):
            event = Event.objects.order_by("?").first()
            if not event:
                self.stdout.write(
                    self.style.ERROR("No events found. please seed events first.")
                )
                return
            ticket_data = factory.create(event=event)
            ticket = Ticket.objects.create(**ticket_data)
            ticket.save()
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} tickets"))


class OrderSeeder(AbstractSeeder):

    def seed(self, *args, **kwargs):
        order_factory = OrderFactory()
        count = kwargs.get("count", 10)
        orders_created = 0

        attendees = list(
            CustomUser.objects.filter(user_type=CustomUser.UserType.ATTENDEE).order_by(
                "?"
            )
        )
        if not attendees:
            self.stdout.write(
                self.style.ERROR("No attendees found. Please seed attendees first.")
            )
            return

        events = list(
            Event.objects.annotate(
                sold_tickets=Count(
                    "tickets", filter=Q(tickets__attendee__isnull=False)
                ),
                total_tickets=F("tickets_amount"),
            )
            .filter(sold_tickets__lt=F("tickets_amount"))
            .order_by("?")
        )  # pick a random event that still has unsold tickets
        if not events:
            self.stdout.write(self.style.ERROR("No available events found."))
            return

        order_item_factory = OrderItemFactory()
        for _ in range(count):
            attendee = random.choice(attendees)
            event = random.choice(events)
            item_quantity = random.randint(1, 3)

            try:
                with transaction.atomic():

                    order_data = order_factory.create(
                        attendee=attendee,
                        total_price=event.ticket_price * item_quantity,
                    )
                    order = Order.objects.create(**order_data)

                    order_item_data = order_item_factory.create(
                        attendee=attendee,
                        order=order,
                        event=event,
                        ticket_price=event.ticket_price,
                        quantity=item_quantity,
                    )

                    OrderItem.objects.create(**order_item_data)

                    orders_created += 1
            except IntegrityError as e:
                self.stdout.write(self.style.WARNING(f"DB Integrety Error: {e}"))
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {orders_created} orders with items"
            )
        )
