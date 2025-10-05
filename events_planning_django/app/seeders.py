from .factories import UserFactory , EventFactory
from .models import CustomUser , Event , Ticket
from abc import ABC , abstractmethod

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
            user = CustomUser.objects.filter(user_type=CustomUser.UserType.ORGANISER).order_by('?').first()
            if not user:
                self.stdout.write(self.style.ERROR("No organiser users found. Please seed organiser users first."))
                return
            event_data = factory.create(organiser=user)
            event = Event.objects.create(**event_data)
            event.save()
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} events"))
        

class TicketSeeder(AbstractSeeder):
    
    def seed(self, *args, **kwargs):
        count = kwargs.get("count", 10)
        for _ in range(count):
            event = Event.objects.order_by('?').first()
            if not event:
                self.stdout.write(self.style.ERROR("No events found. Please seed events first."))
                return
            user = CustomUser.objects.filter(user_type=CustomUser.UserType.ATTENDEE).order_by('?').first()
            if not user:
                self.stdout.write(self.style.ERROR("No attendee users found. Please seed attendee users first."))
                return
            ticket_code = f"TICKET-{event.id}-{user.id}-{_}"
            seat_number = f"SEAT-{_+1}"
            ticket = Ticket.objects.create(
                event=event,
                ticket_code=ticket_code,
                seat_number=seat_number,
                attendee=user
            )
            ticket.save()
        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} tickets"))