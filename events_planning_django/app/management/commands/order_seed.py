from django.core.management.base import BaseCommand, CommandError
from app.factories.order_factory import OrderFactory, Order
from app.factories.order_item_factory import OrderItemFactory
from app.models import CustomUser, Event


class Command(BaseCommand):
    help = "Seed orders into database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            help="Number of orders to create",
            required=False,
            default=10,
        )

    def handle(self, *args, **options):
        try:
            attendee = (
                CustomUser.objects.filter(user_type=CustomUser.UserType.ATTENDEE)
                .order_by("?")
                .first()
            )
            orders = OrderFactory(
                attendee=attendee, order_status=Order.Status.PENDING
            ).seed(count=options["count"])
            for order in orders:
                event = (
                    Event.objects.filter(
                        event_status__in=[
                            Event.Status.UPCOMING,
                            Event.Status.POSTPONED,
                        ]
                    )
                    .order_by("?")
                    .first()
                )
                item = OrderItemFactory(order=order, event=event).create()
                order.total_price = event.ticket_price * item.quantity
                order.save()

        except Exception as e:
            raise CommandError(f"Error seeding orders: {e}")
