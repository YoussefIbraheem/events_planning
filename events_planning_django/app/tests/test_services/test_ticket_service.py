import pytest
from django.utils import timezone
from django.db import transaction
from app.models import Ticket, Event, Order, OrderItem, CustomUser
from app.services.tickets import TicketService
from django.db.models.signals import post_save
from app.signals import generate_tickets


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestTicketService:

    @pytest.fixture
    def attendee(self, django_user_model):
        return django_user_model.objects.create_user(
            username="attendee",
            password="pass123",
            user_type=CustomUser.UserType.ATTENDEE,
        )

    @pytest.fixture
    def organiser(self, django_user_model):
        return django_user_model.objects.create_user(
            username="organiser",
            password="pass123",
            user_type=CustomUser.UserType.ORGANISER,
        )

    @pytest.fixture
    def event(self, organiser):
        return Event.objects.create(
            title="Music Fest",
            description="Summer concert",
            coordinates={"lat": 0, "lng": 0},
            date_time=timezone.now() + timezone.timedelta(days=3),
            tickets_amount=10,
            ticket_price=100,
            organiser=organiser,
        )

    @pytest.fixture
    def tickets(self, event):
        TicketService.increase_tickets(event, 10)
        return Ticket.objects.filter(event=event)

    @pytest.fixture
    def order_with_items(self, attendee, event):
        order = Order.objects.create(
            attendee=attendee, order_status=Order.Status.PENDING
        )
        OrderItem.objects.create(
            order=order, event=event, ticket_price=event.ticket_price, quantity=3
        )
        return order

    # --- TESTS ---

    def test_reserve_tickets_success(self, order_with_items, tickets):
        """Should reserve the requested number of tickets and mark order as RESERVED."""
        order = order_with_items
        TicketService.reserve_tickets(order)

        reserved_tickets = Ticket.objects.filter(order_item__order=order)
        assert reserved_tickets.count() == 3

        # Ensure reserved_until set
        assert all(t.reserved_until is not None for t in reserved_tickets)
        assert order.order_status == Order.Status.RESERVED

    def test_reserve_tickets_fails_if_not_enough_available(
        self, order_with_items, event
    ):
        """Should raise ValueError if insufficient available tickets."""
        # Mark all tickets for the event as already reserved
        other_order = Order.objects.create(
            attendee=order_with_items.attendee, order_status=Order.Status.RESERVED
        )
        other_item = OrderItem.objects.create(
            order=other_order, event=event, ticket_price=event.ticket_price, quantity=10
        )

        tickets = Ticket.objects.filter(event=event)[:10]
        for ticket in tickets:
            ticket.order_item = other_item

        Ticket.objects.bulk_update(tickets, ["order_item"])

        with pytest.raises(ValueError):
            TicketService.reserve_tickets(order_with_items)

    def test_reserve_tickets_fails_if_no_items(self, attendee):
        """Should raise ValueError if order has no items."""
        order = Order.objects.create(
            attendee=attendee, order_status=Order.Status.PENDING
        )
        with pytest.raises(ValueError):
            TicketService.reserve_tickets(order)

    def test_finalize_order_success(self, order_with_items, tickets):
        """Should assign attendee and mark order as PAID."""
        order = order_with_items
        TicketService.reserve_tickets(order)

        TicketService.finalize_order(order)

        sold_tickets = Ticket.objects.filter(order_item__order=order)
        assert sold_tickets.count() == 3
        assert all(t.attendee == order.attendee for t in sold_tickets)
        assert all(t.reserved_until is None for t in sold_tickets)
        order.refresh_from_db()
        assert order.order_status == Order.Status.PAID

    def test_finalize_order_fails_if_not_reserved(self, order_with_items):
        """Should raise ValueError if order not in RESERVED state."""
        order = order_with_items
        assert order.order_status == Order.Status.PENDING

        with pytest.raises(ValueError):
            TicketService.finalize_order(order)

    def test_release_reservation_success(self, order_with_items, tickets):
        """Should clear reserved tickets and mark order as CANCELLED."""
        order = order_with_items
        TicketService.reserve_tickets(order)
        reserved_tickets = Ticket.objects.filter(order_item__order=order)
        assert reserved_tickets.exists()

        TicketService.release_reservation(order)

        # Verify release
        for t in reserved_tickets:
            t.refresh_from_db()
            assert t.order_item is None
            assert t.reserved_until is None

        order.refresh_from_db()
        assert order.order_status == Order.Status.CANCELLED
