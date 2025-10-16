import pytest
from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from django.db.models.signals import post_save
from app.models import Ticket, Event, Order, OrderItem, CustomUser
from app.services.tickets import TicketService
from app.signals import generate_tickets
from app.factories import factories


# * -----------------------------------
# * GLOBAL FIXTURES FOR CLEAN STATE
# * -----------------------------------


@pytest.fixture(autouse=True)
def clear_cache_and_signals():
    """Ensure cache and signals are reset before/after each test."""
    cache.clear()
    post_save.disconnect(generate_tickets, sender=Event)
    yield
    cache.clear()
    post_save.connect(generate_tickets, sender=Event)


@pytest.mark.django_db(transaction=True, reset_sequences=True)
class TestTicketService:

    # * --------------------------
    # * BASE FIXTURES
    # * --------------------------

    @pytest.fixture
    def attendee(self):
        return factories.UserFactory(user_type=CustomUser.UserType.ATTENDEE).create()

    @pytest.fixture
    def organiser(self):
        return factories.UserFactory(user_type=CustomUser.UserType.ORGANISER).create()

    @pytest.fixture
    def event(self, organiser):
        """Create a unique event with fresh tickets each time."""
        event = factories.EventFactory(organiser=organiser).create()
        TicketService.increase_tickets(event, 10)
        return event

    @pytest.fixture
    def tickets(self, event):
        return Ticket.objects.filter(event=event)

    @pytest.fixture
    def order_with_items(self, attendee, event):
        """Create an order linked to an event."""
        order = factories.OrderFactory(
            attendee=attendee, order_status=Order.Status.PENDING
        ).create()
        factories.OrderItemFactory(order=order, event=event, quantity=3).create()
        return order

    # * --------------------------
    # * TESTS
    # * --------------------------

    def test_reserve_tickets_success(self, order_with_items, tickets):
        """Should reserve the requested number of tickets and mark order as RESERVED."""
        order = order_with_items
        TicketService.reserve_tickets(order)

        reserved_tickets = Ticket.objects.filter(order_item__order=order)
        assert reserved_tickets.count() == 3
        assert all(t.reserved_until is not None for t in reserved_tickets)
        order.refresh_from_db()
        assert order.order_status == Order.Status.RESERVED

    def test_reserve_tickets_fails_if_not_enough_available(
        self, order_with_items, event
    ):
        """Should raise ValueError if insufficient available tickets."""
        # Reserve all tickets for another order
        other_order = factories.OrderFactory(
            attendee=order_with_items.attendee,
            order_status=Order.Status.RESERVED,
        ).create()
        
        order_item = factories.OrderItemFactory(
            order=other_order, event=event, quantity=10
        ).create()

        tickets = Ticket.objects.filter(event=event)[:10]
        for ticket in tickets:
            ticket.order_item = order_item
        Ticket.objects.bulk_update(tickets, ["order_item"])

        with pytest.raises(ValueError):
            TicketService.reserve_tickets(order_with_items)

    def test_reserve_tickets_fails_if_no_items(self, attendee):
        """Should raise ValueError if order has no items."""
        order = factories.OrderFactory(
            attendee=attendee, order_status=Order.Status.PENDING
        ).create()
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
