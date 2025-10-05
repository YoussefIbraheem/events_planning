from django.core.management.base import BaseCommand , CommandError
from app.seeders import TicketSeeder



class Command(BaseCommand):
    help = "Seed tickets into database"
    
    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, help="Number of tickets to create", required=False , default=10)

    def handle(self, *args, **options):
        try:
            TicketSeeder.seed(self, count=options["count"])
        except Exception as e:
            raise CommandError(f"Error seeding tickets: {e}")