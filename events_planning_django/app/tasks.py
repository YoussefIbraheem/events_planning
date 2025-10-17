from .models import Ticket, Order
import datetime
from django.db import transaction
from django.utils import timezone
from celery import shared_task
import logging


logger = logging.getLogger("app")


@shared_task
def log_test():
    logger.info("✅ Logger works from inside Celery task!")
    print("✅ Print also works!")


@shared_task
@transaction.atomic
def release_expired_tickets():
    now = timezone.now()

    expired_tickets = Ticket.objects.select_related("order_item__order").filter(
        reserved_until__lte=now, order_item__isnull=False
    )

    if not expired_tickets.exists():
        logger.info("[Celery] No expired tickets found.")
        return "No expired tickets."

    affected_orders = set()
    for ticket in expired_tickets:
        if ticket.order_item and ticket.order_item.order:
            affected_orders.add(ticket.order_item.order.id)

        ticket.order_item = None
        ticket.reserved_until = None

    Ticket.objects.bulk_update(expired_tickets, ["reserved_until", "order_item"])
    logger.info(f"[Celery] Released {expired_tickets.count()} expired tickets.")

    for order_id in affected_orders:
        order = Order.objects.get(id=order_id)

        still_reserved = Ticket.objects.filter(
            order_item__order=order, reserved_until__gt=now
        ).exists()

        if not still_reserved and order.order_status == Order.Status.RESERVED:
            order.order_status = Order.Status.EXPIRED
            order.save(update_fields=["order_status"])
            logger.info(f"[Celery] Marked Order #{order.id} as EXPIRED.")

    logger.info(f"{len(affected_orders)} orders.")
