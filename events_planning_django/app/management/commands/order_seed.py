from django.core.management.base import BaseCommand, CommandError
from app.seeders import OrderSeeder


class Command(BaseCommand):
    help = "Seed orders into database"
    
    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, help="Number of orders to create", required=False , default=10)

    def handle(self, *args, **options):
        try:
            OrderSeeder.seed(self, count=options["count"])
        except Exception as e:
            raise CommandError(f"Error seeding orders: {e}")