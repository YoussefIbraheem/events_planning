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
            status__in=[Order.Status.PENDING, Order.Status.RESERVED],
        ).first()

        if existing_order:
            raise ValueError("You already have an active order.")

        order = Order.objects.create(
            attendee=user,
            payment_method=payment_method,
            status=Order.Status.PENDING,
        )

        for item_data in items_data:
            event = Event.objects.get(pk=item_data["event_id"])

            sold_tickets = Ticket.objects.filter(
                event=event, attendee__isnull=False
            ).count()
            if sold_tickets + item_data["quantity"] > event.tickets_amount:
                raise ValueError(
                    f"Not enough tickets available for event '{event.title}'"
                )

            OrderItem.objects.create(
                order=order,
                event=event,
                quantity=item_data["quantity"],
                ticket_price=event.ticket_price,
            )

        return order

    @classmethod
    @transaction.atomic
    def update_order(cls, user, order, validated_data):
        
        if order.status != Order.Status.PENDING:
            raise ValueError(f"Order is in {order.status} state and cannot be updated!")

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
