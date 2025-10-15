from django.db import transaction
from app.models import OrderItem, Order, Event, Ticket
from rest_framework.response import Response
from rest_framework import status
from collections import defaultdict, Counter


class OrderService:

    @staticmethod
    def _sync_order_items(items):
        """Merge duplicate event items by summing their quantities."""
        merged = Counter()
        for item in items:
            merged[item["event_id"]] += item["quantity"]

        return [{"event_id": eid, "quantity": qty} for eid, qty in merged.items()]

    @classmethod
    @transaction.atomic
    def create_order(cls, user, validated_data):
        items_data = cls._sync_order_items(validated_data["items"])
        payment_method = validated_data["payment_method"]

        existing_order = Order.objects.filter(
            attendee=user,
            order_status__in=[Order.Status.PENDING, Order.Status.RESERVED],
        ).first()

        if existing_order:
            raise ValueError("You already have an active order.")

        event_ids = [i["event_id"] for i in items_data]
        events = {e.id: e for e in Event.objects.filter(id__in=event_ids)}

        order = Order.objects.create(
            attendee=user,
            payment_method=payment_method,
            order_status=Order.Status.PENDING,
        )

        new_items = []
        adding_item_errors = []
        order_total_price = 0

        for item in items_data:
            event = events.get(item["event_id"])

            if not event:
                adding_item_errors.append(
                    f"Event with ID {item['event_id']} not found."
                )
                continue

            if event.event_status not in [
                Event.Status.UPCOMING,
                Event.Status.POSTPONED,
            ]:
                adding_item_errors.append(
                    f"Event '{event.title}' is not open for booking (status: {event.event_status})."
                )
                continue

            sold_tickets = event.tickets.filter(attendee__isnull=False).count()
            if sold_tickets + item["quantity"] > event.tickets_amount:
                adding_item_errors.append(f"Not enough tickets for {event.title}")
                continue

            new_item = OrderItem(
                order=order,
                event=event,
                quantity=item["quantity"],
                ticket_price=event.ticket_price,
            )
            new_items.append(new_item)
            order_total_price += event.ticket_price * item["quantity"]

        if not new_items or adding_item_errors:
            order.delete()
            raise ValueError(", ".join(adding_item_errors))

        OrderItem.objects.bulk_create(new_items)
        order.total_price = order_total_price
        order.save(update_fields=["total_price"])

        return order

    @classmethod
    @transaction.atomic
    def update_order(cls, user, order, validated_data):

        if order.order_status != Order.Status.PENDING:
            raise ValueError(
                f"Order is in {order.order_status} state and cannot be updated!"
            )

        new_items_data = cls._sync_order_items(validated_data["items"])
        payment_method = validated_data["payment_method"]

        order.items.all().delete()

        new_items = []
        new_total_price = 0

        for item in new_items_data:
            event = Event.objects.get(id=item["event_id"])
            quantity = item["quantity"]
            new_item = OrderItem(
                event=event,
                quantity=quantity,
                order=order,
                ticket_price=event.ticket_price,
            )
            new_items.append(new_item)
            new_total_price += event.ticket_price * quantity

        OrderItem.objects.bulk_create(new_items)
        order.payment_method = payment_method
        order.total_price = new_total_price

        order.save(update_fields=["payment_method"])

        return order
