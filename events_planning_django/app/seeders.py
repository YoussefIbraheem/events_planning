from .factories import UserFactory, EventFactory, TicketFactory
from .models import CustomUser, Event, Ticket
from abc import ABC, abstractmethod


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
        count = kwargs.get("count", 10)
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
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} events"))


class TicketSeeder(AbstractSeeder):

    def seed(self, *args, **kwargs):
        factory = TicketFactory()
        count = kwargs.get("count", 10)
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
