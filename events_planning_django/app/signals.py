from django.db.models.signals import post_save, pre_save
import logging
from django.dispatch import receiver
from .models import Event, Ticket
import datetime
import uuid

logger = logging.getLogger("app")


@receiver(post_save, sender=Event)
def generate_tickets(sender, instance, created, **kwargs):
    if created:
        tickets_amounts = instance.tickets_available
        Ticket.increase_tickets(instance, tickets_amounts)
        logger.info(f"Generated {tickets_amounts} tickets for event {instance.id}")


import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Event, Ticket

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Event)
def handle_ticket_amount_change(sender, instance, **kwargs):
    if not instance.id:
        return  # New event — no old instance to compare

    try:
        old_instance = Event.objects.get(id=instance.id)
    except Event.DoesNotExist:
        return

    old_tickets_amount = old_instance.tickets_available
    new_tickets_amount = instance.tickets_available

    if old_tickets_amount == new_tickets_amount:
        return

    difference = new_tickets_amount - old_tickets_amount

    logger.debug(
        f"Old tickets: {old_tickets_amount}, New tickets: {new_tickets_amount}, Difference: {difference}"
    )

    if difference > 0:
        Ticket.increase_tickets(instance, difference)

    elif difference < 0:
        unsold_qs = Ticket.objects.filter(event=instance, attendee__isnull=True)
        available_unsold = unsold_qs.count()
        if available_unsold < abs(difference):
            logger.warning(
                f"Not enough unsold tickets to remove for event {instance.id}. "
                f"Requested: {abs(difference)}, Available: {available_unsold}"
            )
        tickets_to_delete = list(
            unsold_qs[: abs(difference)].values_list("id", flat=True)
        )
        unsold_qs.filter(id__in=tickets_to_delete).delete()
