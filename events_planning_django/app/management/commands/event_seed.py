from django.core.management.base import BaseCommand, CommandError
from app.seeders import EventSeeder


class Command(BaseCommand):
    help = "Seed events into database"
    
    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, help="Number of events to create", required=False , default=10)

    def handle(self, *args, **options):
        try:
            EventSeeder.seed(self, count=options["count"])
        except Exception as e:
            raise CommandError(f"Error seeding events: {e}")