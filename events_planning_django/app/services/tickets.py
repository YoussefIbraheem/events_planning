from django.db import transaction
from django.utils import timezone
from app.models import Ticket, Order
from logging import getLogger
from datetime import datetime
import uuid

logger = getLogger("app")


class TicketService:

    @staticmethod
    @transaction.atomic
    def reserve_tickets(order: Order):

        items = order.items.all()
        if not items:
            raise ValueError("There are no items in the assigned order!")

        to_reserve_tickets = []
        estimated_tickets_count = 0
        for item in items:
            estimated_tickets_count += item.quantity
            available_tickets = list(
                Ticket.objects.select_for_update(skip_locked=True).filter(
                    event=item.event, order_item__isnull=True, attendee__isnull=True
                )[: item.quantity]
            )

            if len(available_tickets) < item.quantity:
                raise ValueError(
                    "Could not get the suiffient amount of tickets! Please check the availablity of tickets."
                )

            now = timezone.now()
            ttl = now + timezone.timedelta(minutes=15)

            for ticket in available_tickets:
                ticket.order_item = item
                ticket.reserved_until = ttl
                to_reserve_tickets.append(ticket)

        Ticket.objects.bulk_update(to_reserve_tickets, ["order_item", "reserved_until"])
        order.status = Order.Status.RESERVED
        order.save(update_fields=["status"])
        logger.info("All tickets have been reserved successfully\n")
        logger.info(f"Attendee:{order.attendee.username}\n")
        logger.info(f"tickets amount:{estimated_tickets_count}")

    @staticmethod
    @transaction.atomic
    def finalize_order(order: Order):

        if order.status != Order.Status.RESERVED:

            raise ValueError("Order is not in reserved state")

        tickets = Ticket.objects.filter(order_item__order=order)

        for ticket in tickets:
            ticket.attendee = order.attendee
            ticket.reserved_until = None

        Ticket.objects.bulk_update(tickets, ["attendee", "reserved_until"])
        order.status = Order.Status.PAID
        order.save()

    @staticmethod
    def release_reservation(order):

        tickets = Ticket.objects.filter(order_item__order=order)
        for t in tickets:
            t.order_item = None
            t.reserved_until = None
        Ticket.objects.bulk_update(tickets, ["order_item", "reserved_until"])
        order.status = Order.Status.CANCELLED
        order.save()

    @staticmethod
    def increase_tickets(event, amount):
        event_date_time = event.date_time
        timestamp = datetime.strftime(event_date_time, "%Y%m%d%H%M%S")
        tickets = [
            Ticket(
                ticket_code=f"{event.id}-{event.organiser.id}-{timestamp}-{i+1}-{uuid.uuid4().hex[:6]}",
                event=event,
            )
            for i in range(amount)
        ]
        Ticket.objects.bulk_create(tickets)
