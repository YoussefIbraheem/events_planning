from django.core.management.base import BaseCommand, CommandError
from app.factories.ticket_factory import TicketFactory
from app.models import Event


class Command(BaseCommand):
    help = "Seed tickets into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            help="Number of tickets to create",
            required=False,
            default=10,
        )

    def handle(self, *args, **options):
        try:
            event = Event.objects.order_by("?").first()
            TicketFactory(event=event).seed(count=options["count"])
        except Exception as e:
            raise CommandError(f"Error seeding tickets: {e}")
