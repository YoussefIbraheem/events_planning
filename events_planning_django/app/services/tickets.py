from django.db import transaction
from django.utils import timezone
from app.models import Ticket, Order
from logging import getLogger

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

            for ticket in available_tickets:
                ticket.order_item = item
                to_reserve_tickets.append(ticket)

        Ticket.objects.bulk_update(to_reserve_tickets, ["order_item"])
        order.status = Order.Status.RESERVED
        order.save(update_fields=["status"])
        logger.info("All tickets have been reserved successfully\n")
        logger.info(f"Attendee:{order.attendee.username}\n")
        logger.info(f"tickets amount:{estimated_tickets_count}")
