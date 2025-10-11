import pytest
from django.db import IntegrityError
from app.models import Event, Ticket, Order, OrderItem, CustomUser
from app.services.tickets import TicketService
from datetime import datetime , timezone
@pytest.mark.django_db
def test_reserve_tickets_successfully_creates_reservations():
    # Arrange
    user = CustomUser.objects.create(username="attendee1")
    event = Event.objects.create(
        title="Music Festival",
        description="Summer fun",
        tickets_amount=10,
        ticket_price=100.00,
        date_time= datetime(2025, 12, 31, 18, 0, tzinfo=timezone.utc),
        organiser=user,
    )
    # Pre-generate tickets
    Ticket.increase_tickets(event, 10)

    order = Order.objects.create(attendee=user, status=Order.Status.PENDING)
    item = OrderItem.objects.create(order=order, event=event, quantity=3, ticket_price=event.ticket_price)

    # Act
    TicketService.reserve_tickets(order)

    # Assert
    reserved_tickets = Ticket.objects.filter(order_item=item)
    assert reserved_tickets.count() == 3
    order.refresh_from_db()
    assert order.status == Order.Status.RESERVED
