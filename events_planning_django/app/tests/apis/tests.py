import json
import random
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from app.models import CustomUser, Event, Ticket, Order, OrderItem
from rest_framework.authtoken.models import Token

# ---------------------------
# pytest fixtures
# ---------------------------

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organiser(db):
    return CustomUser.objects.create_user(
        username="org1",
        email="org1@example.com",
        password="password",
        user_type=CustomUser.UserType.ORGANISER,
    )


@pytest.fixture
def attendee(db):
    return CustomUser.objects.create_user(
        username="att1",
        email="att1@example.com",
        password="password",
        user_type=CustomUser.UserType.ATTENDEE,
    )


@pytest.fixture
def auth_client(api_client, attendee):
    token = Token.objects.create(user=attendee)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def auth_org_client(api_client, organiser):
    token = Token.objects.create(user=organiser)
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return api_client


@pytest.fixture
def event(db, organiser):
    e = Event.objects.create(
        title="Concert",
        description="A test event",
        coordinates={"lat": 0.0, "lng": 0.0},
        date_time=timezone.now() + timezone.timedelta(days=7),
        tickets_amount=10,
        ticket_price=50.0,
        organiser=organiser,
        event_status=Event.Status.UPCOMING,
    )
    # Make sure tickets exist (many projects auto-generate on post_save)
    # if your project uses post_save to create tickets, creation may already happen.
    # Create tickets explicitly for tests (safe w/ unique ticket_code)
    for i in range(10):
        Ticket.objects.create(
            event=e, ticket_code=f"t-{e.id}-{i}-{random.randint(1,10000)}"
        )
    return e


@pytest.fixture
def unbookable_event(db, organiser):
    e = Event.objects.create(
        title="Concert",
        description="A test event",
        coordinates={"lat": 0.0, "lng": 0.0},
        date_time=timezone.now() + timezone.timedelta(days=7),
        tickets_amount=10,
        ticket_price=50.0,
        organiser=organiser,
        event_status=Event.Status.SOON,
    )
    # Make sure tickets exist (many projects auto-generate on post_save)
    # if your project uses post_save to create tickets, creation may already happen.
    # Create tickets explicitly for tests (safe w/ unique ticket_code)
    for i in range(10):
        Ticket.objects.create(
            event=e, ticket_code=f"t-{e.id}-{i}-{random.randint(1,10000)}"
        )
    return e


# Helper to create a pending order with items
@pytest.fixture
def pending_order(db, attendee, event):
    order = Order.objects.create(
        attendee=attendee,
        payment_method=Order.PaymentMethod.CASH,
        order_status=Order.Status.PENDING,
        total_price=0,
    )
    # create one item
    OrderItem.objects.create(
        order=order, event=event, ticket_price=event.ticket_price, quantity=1
    )
    return order


# ---------------------------
# Auth tests
# ---------------------------


def test_register_login_logout(api_client):
    # Register
    resp = api_client.post(
        "/api/register/",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "pass1234",
            "password2": "pass1234",
        },
        format="json",
    )
    assert resp.status_code == status.HTTP_201_CREATED
    assert "access_token" in resp.data

    # Login
    resp = api_client.post(
        "/api/login/",
        data={"username": "newuser", "password": "pass1234"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    assert "access_token" in resp.data

    # Logout
    # Need to include credentials for logout if your view relies on session
    token = resp.data["access_token"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    resp = api_client.post("/api/logout/")
    assert resp.status_code == status.HTTP_200_OK


# ---------------------------
# Event endpoints
# ---------------------------


def test_event_create_requires_organiser(api_client, attendee):
    # attendee tries to create event -> forbidden
    api_client.login(username=attendee.username, password="password")
    resp = api_client.post(
        "/api/events/",
        data={
            "title": "Bad event",
            "description": "desc",
            "coordinates": {"lat": 1, "lng": 2},
            "date_time": (timezone.now() + timezone.timedelta(days=1)).isoformat(),
            "tickets_amount": 5,
            "ticket_price": 10.0,
        },
        format="json",
    )
    assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_401_UNAUTHORIZED)


def test_event_create_and_by_organiser(auth_org_client, organiser):
    resp = auth_org_client.post(
        "/api/events/",
        data={
            "title": "My Event",
            "description": "desc",
            "coordinates": {"lat": 1, "lng": 2},
            "date_time": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
            "tickets_amount": 5,
            "ticket_price": 20.0,
        },
        format="json",
    )
    assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)

    # test by_organiser endpoint
    resp = auth_org_client.get(f"/api/events/organiser/{organiser.id}/")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.data, list) or "results" in resp.data


def test_event_list_public(api_client, event):
    resp = api_client.get("/api/events/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) >= 1


# ---------------------------
# Ticket endpoints & filtering
# ---------------------------


def test_ticket_list_filters(auth_org_client, event):
    # organiser can list tickets for own events
    resp = auth_org_client.get("/api/tickets/", {"event_id": event.id})
    assert resp.status_code == status.HTTP_200_OK
    # ensure response contains tickets
    if isinstance(resp.data, dict):
        # paginated or filtered output
        items = resp.data.get("results", resp.data.get("data", []))
    else:
        items = resp.data
    assert len(items) >= 1


# ---------------------------
# Order endpoints
# ---------------------------


def test_create_order_requires_items(auth_client):
    # Missing items -> bad request
    resp = auth_client.post(
        "/api/orders/", data={"payment_method": Order.PaymentMethod.CASH}, format="json"
    )
    assert (
        resp.status_code == status.HTTP_400_BAD_REQUEST
        or resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    )


def test_create_order_success(auth_client, event, attendee):
    # create order payload that frontend would send (items list)
    payload = {
        "items": [
            {"event_id": event.id, "quantity": 2},
        ],
        "payment_method": Order.PaymentMethod.CASH,
    }
    resp = auth_client.post("/api/orders/", data=payload, format="json")
    assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    # check order recorded
    order_id = resp.data.get("id") or resp.data.get("order", {}).get("id")
    if not order_id:
        # sometimes serializer.instance was returned - find by attendee
        order = Order.objects.filter(attendee=attendee).order_by("-id").first()
    else:
        order = Order.objects.get(id=order_id)
    assert order.items.count() >= 1
    assert order.order_status == Order.Status.PENDING


def test_prevent_multiple_pending_orders(auth_client, event, attendee):
    # Create a pending order
    payload = {
        "items": [{"event_id": event.id, "quantity": 1}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    resp1 = auth_client.post("/api/orders/", data=payload, format="json")

    assert resp1.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)

    # Try to create another pending order -> should be rejected
    resp2 = auth_client.post("/api/orders/", data=payload, format="json")

    assert resp2.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
    )


def test_update_order_only_pending(auth_client, pending_order, event):
    # mark as RESERVED and attempt update -> should be disallowed
    pending_order.order_status = Order.Status.RESERVED
    pending_order.save(update_fields=["order_status"])
    payload = {
        "items": [{"event_id": event.id, "quantity": 2}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    resp = auth_client.put(
        f"/api/orders/{pending_order.id}/", data=payload, format="json"
    )
    assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)


def test_update_order_success(auth_client, pending_order, event):
    # ensure pending order can be updated
    pending_order.order_status = Order.Status.PENDING
    pending_order.save(update_fields=["order_status"])
    payload = {
        "items": [{"event_id": event.id, "quantity": 2}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    resp = auth_client.put(
        f"/api/orders/{pending_order.id}/", data=payload, format="json"
    )
    assert resp.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
    # assert DB updated
    pending_order.refresh_from_db()
    assert pending_order.items.count() >= 1


def test_cannot_create_order_with_unbookable_event(
    auth_client, unbookable_event, attendee
):

    payload = {
        "items": [
            {"event_id": unbookable_event.id, "quantity": 2},
        ],
        "payment_method": Order.PaymentMethod.CASH,
    }

    resp = auth_client.post("/api/orders/", data=payload, format="json")
    assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)


# ---------------------------
# Checkout / Reserve / Finalize / Cancel flows
# ---------------------------


def test_checkout_reserves_tickets(auth_client, attendee, event):
    # Create order with items
    payload = {
        "items": [{"event_id": event.id, "quantity": 2}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    create_resp = auth_client.post("/api/orders/", data=payload, format="json")
    assert create_resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    # find order
    order = Order.objects.filter(attendee=attendee).order_by("-id").first()
    assert order is not None

    # call checkout
    resp = auth_client.post(f"/api/orders/{order.id}/checkout/")
    assert resp.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    assert order.order_status == Order.Status.RESERVED

    # check tickets reserved: tickets should have order_item set and reserved_until not None
    tickets = Ticket.objects.filter(order_item__order=order)
    assert tickets.count() >= 1
    for t in tickets:
        assert t.order_item is not None
        assert t.reserved_until is not None


def test_finalize_sets_attendee_and_clears_reservation(auth_client, attendee, event):
    # create & checkout
    payload = {
        "items": [{"event_id": event.id, "quantity": 2}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    auth_client.post("/api/orders/", data=payload, format="json")
    order = Order.objects.filter(attendee=attendee).order_by("-id").first()
    assert order is not None
    auth_client.post(f"/api/orders/{order.id}/checkout/")

    # finalize
    resp = auth_client.post(
        f"/api/orders/{order.id}/finalise/"
    )  # note: view uses 'finalise' path
    assert resp.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    assert order.order_status == Order.Status.PAID
    tickets = Ticket.objects.filter(order_item__order=order)
    for t in tickets:
        assert t.attendee == attendee
        assert t.reserved_until is None


def test_cancel_releases_tickets(auth_client, attendee, event):
    # create, checkout, then cancel
    payload = {
        "items": [{"event_id": event.id, "quantity": 1}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    auth_client.post("/api/orders/", data=payload, format="json")
    order = Order.objects.filter(attendee=attendee).order_by("-id").first()
    auth_client.post(f"/api/orders/{order.id}/checkout/")

    # cancel
    resp = auth_client.post(f"/api/orders/{order.id}/cancel/")
    assert resp.status_code == status.HTTP_200_OK

    order.refresh_from_db()
    assert order.order_status == Order.Status.CANCELLED
    tickets = Ticket.objects.filter(order_item__order=order)
    # after release order_item should be None
    for t in tickets:
        assert t.order_item is None
        assert t.attendee is None


# ---------------------------
# Permissions and edge cases
# ---------------------------


def test_attendee_cannot_list_other_users_orders(auth_client, attendee):
    # create order for another user and ensure current attendee cannot see it
    other = CustomUser.objects.create_user(
        username="other",
        email="o@example.com",
        password="pass",
        user_type=CustomUser.UserType.ATTENDEE,
    )
    order = Order.objects.create(
        attendee=other,
        payment_method=Order.PaymentMethod.CASH,
        order_status=Order.Status.PENDING,
    )
    resp = auth_client.get("/api/orders/")
    assert resp.status_code == status.HTTP_200_OK
    # ensure that the returned list does not include other user's order id
    data = resp.data
    # handle pagination shape
    results = data.get("results", data) if isinstance(data, dict) else data
    ids = [o.get("id") for o in results]
    assert order.id not in ids


def test_checkout_fails_if_insufficient_tickets(auth_client, attendee, event):
    # artificially reduce available tickets to 0
    Ticket.objects.filter(event=event, attendee__isnull=True).delete()
    payload = {
        "items": [{"event_id": event.id, "quantity": 1}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    create_resp = auth_client.post("/api/orders/", data=payload, format="json")
    assert create_resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    order = Order.objects.filter(attendee=attendee).order_by("-id").first()
    resp = auth_client.post(f"/api/orders/{order.id}/checkout/")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
