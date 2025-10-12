import logging
import uuid
import datetime
from django.db import transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import Event, Ticket, Order, OrderItem
from app.services.tickets import TicketService

logger = logging.getLogger("app")

# ------------------------------------------------------------
# EVENT TICKET GENERATION & UPDATES
# ------------------------------------------------------------


def generate_tickets(sender, instance: Event, created, **kwargs):
    """Generate initial tickets when a new event is created."""
    if created:
        TicketService.increase_tickets(instance, instance.tickets_amount)
        logger.info(
            f"Generated {instance.tickets_amount} tickets for event {instance.id}"
        )


@receiver(pre_save, sender=Event)
def handle_ticket_amount_change(sender, instance: Event, **kwargs):
    """Increase or decrease tickets when event.tickets_amount changes."""
    if not instance.id:
        return  # new event, handled by post_save above

    try:
        old_instance = Event.objects.get(id=instance.id)
    except Event.DoesNotExist:
        return

    old_amount = old_instance.tickets_amount
    new_amount = instance.tickets_amount
    diff = new_amount - old_amount

    if diff == 0:
        return

    logger.debug(f"Old tickets: {old_amount}, New: {new_amount}, Diff: {diff}")

    if diff > 0:
        TicketService.increase_tickets(event=instance, amount=diff)
        

    elif diff < 0:

        TicketService.decrease_unsold_tickets(event=instance, amount=abs(diff))
        
