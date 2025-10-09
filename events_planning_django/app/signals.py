from django.db.models.signals import post_save, pre_save
import logging
from django.dispatch import receiver
from .models import Event, Ticket, Order, OrderItem
import datetime
import uuid
from django.db import transaction, Q, F

logger = logging.getLogger("app")


@receiver(post_save, sender=Event)
def generate_tickets(instance: Event, sender, created, **kwargs):
    if created:
        tickets_amounts = instance.tickets_amount
        Ticket.increase_tickets(instance, tickets_amounts)
        logger.info(f"Generated {tickets_amounts} tickets for event {instance.id}")


@receiver(pre_save, sender=Event)
def handle_ticket_amount_change(instance: Event, sender, **kwargs):
    if not instance.id:
        return  # New event — no old instance to compare

    try:
        old_instance = Event.objects.get(id=instance.id)
    except Event.DoesNotExist:
        return

    old_tickets_amount = old_instance.tickets_amount
    new_tickets_amount = instance.tickets_amount

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


@receiver(post_save, sender=OrderItem)
def reserve_tickets(instance: OrderItem, sender, created, **kwargs):
    if not created:
        return

    with transaction.atomic():
        event = instance.event
        order = instance.order
        attendee = order.attendee
        quantity = instance.quantity

        available_tickets = list(
            Ticket.objects.select_for_update(skip_locked=True).filter(
                event=event, attendee__isnull=True
            )[:quantity]
        )

        if len(available_tickets) < quantity:

            raise ValueError("Not enough tickets available.")

        for ticket in available_tickets:
            ticket.attendee = attendee

        Ticket.objects.bulk_update(available_tickets, ["attendee"])


@receiver(pre_save, sender=OrderItem)
def handle_quantity_change(instance: OrderItem, **kwargs):
    if not instance.id:
        return

    try:
        old_instance = OrderItem.objects.get(id=instance.id)
    except Event.DoesNotExist:
        return

    event = instance.event
    attendee = instance.order.attendee
    old_quantity = old_instance.quantity
    new_quantity = instance.quantity

    if new_quantity == old_quantity:
        return

    difference = new_quantity - old_quantity

    if difference > 0:

        with transaction.atomic():
            available_tickets = list(
                Ticket.objects.select_for_update(skip_locked=True).filter(
                    event=event, attendee__isnull=True
                )[:difference]
            )

            if len(available_tickets) < difference:
                raise ValueError("Not enough tickets available.")

            for tickets in available_tickets:
                tickets.attendee = attendee
            Ticket.objects.bulk_update(available_tickets, ["attendee"])

    if difference < 0:
        excluded_tickets = list(
            Ticket.objects.select_for_update(skip_locked=True)
            .filter(event=event, attendee=attendee)
            .order_by("-id")[: abs(difference)]
        )

        for ticket in excluded_tickets:
            ticket.attendee = None
        Ticket.objects.bulk_update(excluded_tickets, ["attendee"])
