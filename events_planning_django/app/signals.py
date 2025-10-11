import logging
import uuid
import datetime
from django.db import transaction
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from .models import Event, Ticket, Order, OrderItem

logger = logging.getLogger("app")

# ------------------------------------------------------------
# EVENT TICKET GENERATION & UPDATES
# ------------------------------------------------------------


@receiver(post_save, sender=Event)
def generate_tickets(sender, instance: Event, created, **kwargs):
    """Generate initial tickets when a new event is created."""
    if created:
        tickets_amount = instance.tickets_amount
        Ticket.increase_tickets(instance, tickets_amount)
        logger.info(f"Generated {tickets_amount} tickets for event {instance.id}")


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
        Ticket.increase_tickets(instance, diff)
        logger.info(f"Added {diff} tickets to event {instance.id}")

    elif diff < 0:
        unsold_qs = Ticket.objects.filter(event=instance, attendee__isnull=True)
        available_unsold = unsold_qs.count()

        if available_unsold < abs(diff):
            logger.warning(
                f"Not enough unsold tickets to remove for event {instance.id}. "
                f"Requested: {abs(diff)}, Available: {available_unsold}"
            )

        to_delete_ids = list(unsold_qs.values_list("id", flat=True)[: abs(diff)])
        unsold_qs.filter(id__in=to_delete_ids).delete()
        logger.info(
            f"Removed {len(to_delete_ids)} unsold tickets from event {instance.id}"
        )


# ------------------------------------------------------------
# ORDER ITEM → TICKET RESERVATION
# ------------------------------------------------------------


# @receiver(post_save, sender=OrderItem)
# def reserve_tickets(sender, instance: OrderItem, created, **kwargs):
#     """Reserve tickets when a new order item is created."""
#     if not created:
#         return

#     with transaction.atomic():
#         event = instance.event
#         order = instance.order
#         attendee = order.attendee
#         quantity = instance.quantity

#         available_tickets = list(
#             Ticket.objects.select_for_update(skip_locked=True).filter(
#                 event=event, attendee__isnull=True
#             )[:quantity]
#         )

#         if len(available_tickets) < quantity:
#             raise ValueError("Not enough tickets available.")

#         for ticket in available_tickets:
#             ticket.attendee = attendee
#             ticket.order_item = instance

#         Ticket.objects.bulk_update(available_tickets, ["attendee", "order_item"])
#         logger.info(
#             f"Reserved {len(available_tickets)} tickets "
#             f"for order {order.id} / attendee {attendee.id}"
#         )

# TODO Find another TP 
# ! OrderItem creation WILL NOT reserve the ticket 

# ------------------------------------------------------------
# ORDER ITEM QUANTITY CHANGE HANDLER
# ------------------------------------------------------------


@receiver(pre_save, sender=OrderItem)
def handle_quantity_change(sender, instance: OrderItem, **kwargs):
    """Adjust reserved tickets if order item quantity changes."""
    if not instance.id:
        return

    try:
        old_instance = OrderItem.objects.get(id=instance.id)
    except OrderItem.DoesNotExist:
        return

    event = instance.event
    order = instance.order
    attendee = order.attendee
    old_qty = old_instance.quantity
    new_qty = instance.quantity
    diff = new_qty - old_qty

    if diff == 0:
        return

    with transaction.atomic():
        if diff > 0:
            # reserve additional tickets
            available_tickets = list(
                Ticket.objects.select_for_update(skip_locked=True).filter(
                    event=event, attendee__isnull=True
                )[:diff]
            )

            if len(available_tickets) < diff:
                raise ValueError("Not enough tickets available.")

            for ticket in available_tickets:
                ticket.attendee = attendee
                ticket.order_item = instance

            Ticket.objects.bulk_update(available_tickets, ["attendee", "order_item"])
            logger.info(f"Added {diff} tickets for order item {instance.id}")

        elif diff < 0:
            # release excess tickets
            tickets_to_release = list(
                Ticket.objects.select_for_update(skip_locked=True)
                .filter(order_item=instance, attendee=attendee)
                .order_by("-id")[: abs(diff)]
            )

            for ticket in tickets_to_release:
                ticket.attendee = None
                ticket.order_item = None

            Ticket.objects.bulk_update(tickets_to_release, ["attendee", "order_item"])
            logger.info(f"Released {abs(diff)} tickets for order item {instance.id}")


# ------------------------------------------------------------
# ORDER CANCELLATION HANDLER
# ------------------------------------------------------------


@receiver(post_save, sender=Order)
def handle_order_cancellation(sender, instance: Order, **kwargs):
    """Free tickets when an order is cancelled."""
    if instance.status != instance.Status.CANCELLED:
        return

    with transaction.atomic():
        order_items = instance.items.all()
        released_tickets = list(Ticket.objects.filter(order_item__in=order_items))

        for ticket in released_tickets:
            ticket.attendee = None
            ticket.order_item = None

        Ticket.objects.bulk_update(released_tickets, ["attendee", "order_item"])
        logger.info(
            f"Released {len(released_tickets)} tickets from cancelled order {instance.id}"
        )


@receiver(post_delete, sender=OrderItem)
def release_tickets_on_order_item_delete(sender, instance, **kwargs):
    """Release tickets if an order item is deleted directly."""
    with transaction.atomic():
        tickets = Ticket.objects.filter(order_item=instance)
        for ticket in tickets:
            ticket.attendee = None
            ticket.order_item = None
        Ticket.objects.bulk_update(tickets, ["attendee", "order_item"])
        logger.info(
            f"Released {len(tickets)} tickets due to deletion of order item {instance.id}"
        )


@receiver(post_delete, sender=Order)
def release_tickets_on_order_delete(sender, instance, **kwargs):
    """Release tickets if an entire order is deleted directly."""
    with transaction.atomic():
        tickets = Ticket.objects.filter(order_item__order=instance)
        for ticket in tickets:
            ticket.attendee = None
            ticket.order_item = None
        Ticket.objects.bulk_update(tickets, ["attendee", "order_item"])
        logger.info(
            f"Released {len(tickets)} tickets due to deletion of order {instance.id}"
        )
