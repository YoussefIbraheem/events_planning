import pytest
from django.db import IntegrityError
from app.models import Order, OrderItem, Event, Ticket, CustomUser
from app.services.orders import OrderService
from app.factories import TicketFactory
import datetime


@pytest.mark.django_db(transaction=True)
class TestOrderService:
    # ----------------------------------------------------------------------
    # MISC
    # ----------------------------------------------------------------------
    @pytest.fixture
    def future_datetime(self):
        return datetime.datetime.today() + datetime.timedelta(days=60)

    # ----------------------------------------------------------------------
    # _sync_order_items
    # ----------------------------------------------------------------------
    def test_sync_order_items_merges_duplicates(self):
        items = [
            {"event_id": 1, "quantity": 2},
            {"event_id": 1, "quantity": 3},
            {"event_id": 2, "quantity": 1},
        ]
        merged = OrderService._sync_order_items(items)
        merged_dict = {i["event_id"]: i["quantity"] for i in merged}

        assert merged_dict == {1: 5, 2: 1}

    def test_sync_order_items_returns_empty_if_no_items(self):
        assert OrderService._sync_order_items([]) == []

    # ----------------------------------------------------------------------
    # create_order
    # ----------------------------------------------------------------------
    def test_create_order_success(self, django_db_setup, future_datetime):
        user = CustomUser.objects.create_user(username="testuser", password="123")

        event = Event.objects.create(
            title="Concert",
            description="Test event",
            organiser=user,
            ticket_price=100,
            tickets_amount=10,
            date_time=future_datetime,
        )
        validated_data = {
            "items": [{"event_id": event.id, "quantity": 2}],
            "payment_method": Order.PaymentMethod.CREDIT,
        }

        order = OrderService.create_order(user, validated_data)

        assert order.attendee == user
        assert order.status == Order.Status.PENDING
        assert order.items.count() == 1
        assert order.items.first().quantity == 2

    def test_create_order_raises_if_existing_pending(self, future_datetime):
        user = CustomUser.objects.create_user(username="pending_user", password="123")
        order = Order.objects.create(
            attendee=user,
            payment_method=Order.PaymentMethod.CASH,
            status=Order.Status.PENDING,
        )

        event = Event.objects.create(
            title="Event 1",
            description="Test",
            organiser=user,
            ticket_price=50,
            tickets_amount=5,
            date_time=future_datetime,
        )

        validated_data = {
            "items": [{"event_id": event.id, "quantity": 1}],
            "payment_method": Order.PaymentMethod.CREDIT,
        }

        with pytest.raises(ValueError, match="already have an active order"):
            OrderService.create_order(user, validated_data)

    def test_create_order_raises_if_tickets_insufficient(self, future_datetime):
        user = CustomUser.objects.create_user(
            username="insufficient_user", password="123"
        )
        organiser = CustomUser.objects.create_user(
            username="organiser", password="123", user_type="organiser"
        )
        event = Event.objects.create(
            title="Sold Out Event",
            description="",
            organiser=organiser,
            ticket_price=100,
            tickets_amount=2,
            date_time=future_datetime,
        )

        factory = TicketFactory()
        # Simulate all tickets already sold
        for _ in range(2):
            data = factory.create(event=event, attendee=user)
            Ticket.objects.create(**data)

        validated_data = {
            "items": [{"event_id": event.id, "quantity": 1}],
            "payment_method": Order.PaymentMethod.CREDIT,
        }

        with pytest.raises(ValueError, match="Not enough tickets available"):
            OrderService.create_order(user, validated_data)

    # ----------------------------------------------------------------------
    # update_order
    # ----------------------------------------------------------------------
    def test_update_order_success(self, future_datetime):
        user = CustomUser.objects.create_user(username="update_user", password="123")
        organiser = CustomUser.objects.create_user(
            username="orgu", password="123", user_type="organiser"
        )
        event1 = Event.objects.create(
            title="E1",
            description="",
            organiser=organiser,
            ticket_price=100,
            tickets_amount=10,
            date_time=future_datetime,
        )
        event2 = Event.objects.create(
            title="E2",
            description="",
            organiser=organiser,
            ticket_price=50,
            tickets_amount=10,
            date_time=future_datetime,
        )

        order = Order.objects.create(
            attendee=user,
            payment_method=Order.PaymentMethod.CASH,
            status=Order.Status.PENDING,
        )
        OrderItem.objects.create(
            order=order, event=event1, quantity=2, ticket_price=100
        )

        updated_data = {
            "items": [{"event_id": event2.id, "quantity": 3}],
            "payment_method": Order.PaymentMethod.CREDIT,
        }

        updated_order = OrderService.update_order(user, order, updated_data)

        assert updated_order.payment_method == Order.PaymentMethod.CREDIT
        assert updated_order.items.count() == 1
        new_item = updated_order.items.first()
        assert new_item.event == event2
        assert new_item.quantity == 3

    def test_update_order_fails_if_not_pending(self, future_datetime):
        user = CustomUser.objects.create_user(username="blocked_user", password="123")
        event = Event.objects.create(
            title="Concert",
            description="",
            organiser=user,
            ticket_price=100,
            tickets_amount=10,
            date_time=future_datetime,
        )
        order = Order.objects.create(
            attendee=user,
            payment_method=Order.PaymentMethod.CASH,
            status=Order.Status.PAID,
        )

        validated_data = {
            "items": [{"event_id": event.id, "quantity": 1}],
            "payment_method": Order.PaymentMethod.CREDIT,
        }

        with pytest.raises(ValueError, match="cannot be updated"):
            OrderService.update_order(user, order, validated_data)

    def test_update_order_with_invalid_event_raises(self):
        user = CustomUser.objects.create_user(
            username="invalid_event_user", password="123"
        )
        order = Order.objects.create(
            attendee=user,
            payment_method=Order.PaymentMethod.CASH,
            status=Order.Status.PENDING,
        )

        validated_data = {
            "items": [{"event_id": 999, "quantity": 1}],
            "payment_method": Order.PaymentMethod.CREDIT,
        }

        with pytest.raises(Event.DoesNotExist):
            OrderService.update_order(user, order, validated_data)
