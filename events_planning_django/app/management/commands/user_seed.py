from django.core.management.base import BaseCommand, CommandError
from app.seeders import UserSeeder


class Command(BaseCommand):
    help = "Seed users into database"
    
    
    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, help="Number of users to create", required=False , default=10)
        parser.add_argument("--user_type", type=str, help="Type of users to create (attendee or organiser)",required=False , default="attendee")

    def handle(self, *args, **options):
        
        try:
            UserSeeder.seed(self, count=options["count"], user_type=options["user_type"])
        except Exception as e:
            raise CommandError(f"Error seeding users: {e}")
