from django.core.management.base import BaseCommand, CommandError
from app.factories.factories import EventFactory
from app.models import CustomUser


class Command(BaseCommand):
    help = "Seed events into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            help="Number of events to create",
            required=False,
            default=10,
        )

    def handle(self, *args, **options):
        try:
            count = options["count"]
            organiser = (
                CustomUser.objects.filter(user_type=CustomUser.UserType.ORGANISER)
                .order_by("?")
                .first()
            )
            EventFactory(organiser=organiser).seed(count=count)
        except Exception as e:
            raise CommandError(f"Error seeding events: {e}")
