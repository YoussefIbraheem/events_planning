from .models import Ticket
from datetime import datetime
from django.db import transaction
import logging
from celery import shared_task
logger = logging.getLogger("app")



@shared_task
@transaction.atomic
def release_expired_tickets():
    current_date_time = datetime.now()
    expired_tickets = Ticket.objects.filter(reserved_until__lte=current_date_time).get()

    for ticket in expired_tickets:
        ticket.reserved_until = None
        ticket.order_item = None

    Ticket.objects.bulk_update(expired_tickets, ["reserved_until", "order_item"])

    logger.info(f"tickets of count{expired_tickets.count()} has been released")
