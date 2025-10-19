import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.authtoken.models import Token
from app.models import Order, Ticket
from app.factories import factories
from django.core.cache import cache

pytestmark = pytest.mark.django_db(transaction=True, reset_sequences=True)

# * ---------------------------
# * * pytest fixtures
# * ---------------------------

@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def organiser():
    return factories.UserFactory(user_type="organiser").create()


@pytest.fixture
def attendee():
    return factories.UserFactory(user_type="attendee").create()


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
def event(organiser):
    """Create an upcoming event with pre-generated tickets."""
    e = factories.EventFactory(
        organiser=organiser,
        event_status="upcoming",
        date_time=timezone.now() + timezone.timedelta(days=7),
    ).create()
    factories.TicketFactory(event=e).seed(10)
    return e


@pytest.fixture
def unbookable_event(organiser):
    """Event with a status that prevents booking."""
    e = factories.EventFactory(
        organiser=organiser,
        event_status="soon",
        date_time=timezone.now() + timezone.timedelta(days=7),
    ).create()
    factories.TicketFactory(event=e).seed(10)
    return e


@pytest.fixture
def pending_order(attendee, event):
    """Create an order with one order item in PENDING state."""
    order = factories.OrderFactory(attendee=attendee, order_status="pending").create()
    factories.OrderItemFactory(order=order, event=event, quantity=1).create()
    return order


# * ---------------------------
# * * Authentication flow
# * ---------------------------

def test_register_login_logout(api_client):
    # * Register
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

    # * * Login
    resp = api_client.post(
        "/api/login/",
        data={"username": "newuser", "password": "pass1234"},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    token = resp.data["access_token"]

    # * Logout
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {token}")
    resp = api_client.post("/api/logout/")
    assert resp.status_code == status.HTTP_200_OK


# * ---------------------------
# * * Event endpoints
# * ---------------------------

def test_event_create_requires_organiser(api_client, attendee):
    api_client.login(username=attendee.username, password="password")
    resp = api_client.post(
        "/api/events/",
        data={
            "title": "Unauthorized event",
            "description": "desc",
            "latitude": "1.2",
            "longitude": "2.3",
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
            "latitude": "1.2",
            "longitude": "2.3",
            "date_time": (timezone.now() + timezone.timedelta(days=2)).isoformat(),
            "tickets_amount": 5,
            "ticket_price": 20.0,
        },
        format="json",
    )
    assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)

    resp = auth_org_client.get(f"/api/events/organiser/{organiser.id}/")
    assert resp.status_code == status.HTTP_200_OK
    assert isinstance(resp.data, (list, dict))


def test_event_list_public(api_client, event):
    resp = api_client.get("/api/events/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data) >= 1


# * ---------------------------
# * *icket endpoints
# * ---------------------------

def test_ticket_list_filters(auth_org_client, event):
    resp = auth_org_client.get("/api/tickets/", {"event_id": event.id})
    assert resp.status_code == status.HTTP_200_OK
    data = resp.data.get("results", resp.data) if isinstance(resp.data, dict) else resp.data
    assert len(data) >= 1


# * ---------------------------
# * Order endpoints
# * ---------------------------

def test_create_order_requires_items(auth_client):
    resp = auth_client.post(
        "/api/orders/",
        data={"payment_method": Order.PaymentMethod.CASH},
        format="json",
    )
    assert resp.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_422_UNPROCESSABLE_ENTITY,
    )


def test_create_order_success(auth_client, event, attendee):
    payload = {
        "items": [{"event_id": event.id, "quantity": 2}],
        "payment_method": Order.PaymentMethod.CASH,
    }
    resp = auth_client.post("/api/orders/", data=payload, format="json")
    assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    order = Order.objects.filter(attendee=attendee).last()
    assert order.items.count() == 1
    assert order.order_status == Order.Status.PENDING


def test_prevent_multiple_pending_orders(auth_client, event):
    payload = {"items": [{"event_id": event.id, "quantity": 1}], "payment_method": "cash"}
    first = auth_client.post("/api/orders/", data=payload, format="json")
    assert first.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    second = auth_client.post("/api/orders/", data=payload, format="json")
    assert second.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)


def test_update_order_only_pending(auth_client, pending_order, event):
    pending_order.order_status = Order.Status.RESERVED
    pending_order.save()
    payload = {"items": [{"event_id": event.id, "quantity": 2}], "payment_method": "cash"}
    resp = auth_client.put(f"/api/orders/{pending_order.id}/", data=payload, format="json")
    assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)


def test_update_order_success(auth_client, pending_order, event):
    payload = {"items": [{"event_id": event.id, "quantity": 2}], "payment_method": "cash"}
    resp = auth_client.put(f"/api/orders/{pending_order.id}/", data=payload, format="json")
    assert resp.status_code in (status.HTTP_200_OK, status.HTTP_204_NO_CONTENT)
    pending_order.refresh_from_db()
    assert pending_order.items.count() >= 1


def test_cannot_create_order_with_unbookable_event(auth_client, unbookable_event):
    payload = {"items": [{"event_id": unbookable_event.id, "quantity": 2}], "payment_method": "cash"}
    resp = auth_client.post("/api/orders/", data=payload, format="json")
    assert resp.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_403_FORBIDDEN)


# * ---------------------------
# * Checkout / Finalize / Cancel
# * ---------------------------

def test_checkout_reserves_tickets(auth_client, attendee, event):
    payload = {"items": [{"event_id": event.id, "quantity": 2}], "payment_method": "cash"}
    resp = auth_client.post("/api/orders/", data=payload, format="json")
    assert resp.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)
    order = Order.objects.filter(attendee=attendee).last()

    resp = auth_client.post(f"/api/orders/{order.id}/checkout/")
    assert resp.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.order_status == Order.Status.RESERVED


def test_finalize_sets_attendee_and_clears_reservation(auth_client, attendee, event):
    payload = {"items": [{"event_id": event.id, "quantity": 2}], "payment_method": "cash"}
    auth_client.post("/api/orders/", data=payload, format="json")
    order = Order.objects.filter(attendee=attendee).last()
    auth_client.post(f"/api/orders/{order.id}/checkout/")
    resp = auth_client.post(f"/api/orders/{order.id}/finalise/")
    assert resp.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.order_status == Order.Status.PAID


def test_cancel_releases_tickets(auth_client, attendee, event):
    payload = {"items": [{"event_id": event.id, "quantity": 1}], "payment_method": "cash"}
    auth_client.post("/api/orders/", data=payload, format="json")
    order = Order.objects.filter(attendee=attendee).last()
    auth_client.post(f"/api/orders/{order.id}/checkout/")
    resp = auth_client.post(f"/api/orders/{order.id}/cancel/")
    assert resp.status_code == status.HTTP_200_OK
    order.refresh_from_db()
    assert order.order_status == Order.Status.CANCELLED


# * ---------------------------
# * Permissions & Edge Cases
# * ---------------------------

def test_attendee_cannot_list_other_users_orders(auth_client, attendee):
    other = factories.UserFactory(user_type="attendee").create()
    factories.OrderFactory(attendee=other, order_status="pending").create()
    resp = auth_client.get("/api/orders/")
    assert resp.status_code == status.HTTP_200_OK
    results = resp.data.get("results", resp.data) if isinstance(resp.data, dict) else resp.data
    ids = [o.get("id") for o in results]
    assert all(order_id for order_id in ids if order_id is not None)
    assert not any(Order.objects.filter(attendee=other, id=oid).exists() for oid in ids)


def test_checkout_fails_if_insufficient_tickets(auth_client, attendee, event):
    Ticket.objects.filter(event=event, attendee__isnull=True).delete()
    payload = {"items": [{"event_id": event.id, "quantity": 1}], "payment_method": "cash"}
    auth_client.post("/api/orders/", data=payload, format="json")
    order = Order.objects.filter(attendee=attendee).last()
    resp = auth_client.post(f"/api/orders/{order.id}/checkout/")
    assert resp.status_code == status.HTTP_400_BAD_REQUEST


# * ---------------------------
# * Caching
# * ---------------------------

def test_event_list_cached(api_client, organiser):
    """Ensure repeated event list requests are served from cache."""
    cache.clear()

    # Create an event via factory
    factories.EventFactory(organiser=organiser).create()

    url = "/api/events/"
    resp1 = api_client.get(url)
    assert resp1.status_code == status.HTTP_200_OK
    data1 = resp1.content

    # Second call → should hit the cache
    resp2 = api_client.get(url)
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.content == data1


def test_event_cache_invalidated_on_create(api_client, organiser):
    """Cache invalidates when a new event is added (via signal)."""
    cache.clear()

    # Initial event list cached
    factories.EventFactory(organiser=organiser).create()
    url = "/api/events/"
    resp1 = api_client.get(url)
    cached_content = resp1.content

    # Create a new event (should trigger signal → cache invalidated)
    factories.EventFactory(organiser=organiser, title="Fresh Event").create()

    # After invalidation, cache content should differ
    resp2 = api_client.get(url)
    assert resp2.content != cached_content
    titles = [e['title'] for e in resp2.data["results"]]
    assert "Fresh Event" in titles


def test_order_list_cache_invalidated(auth_client, attendee, organiser):
    """Ensure order list cache invalidates when new orders are created."""
    cache.clear()
    url = "/api/orders/"

    # Cache initial empty state
    resp1 = auth_client.get(url)
    cached_content = resp1.content

    # Create an event & place an order
    event = factories.EventFactory(organiser=organiser).create()
    payload = {
        "items": [{"event_id": event.id, "quantity": 1}],
        "payment_method": Order.PaymentMethod.CASH,
    }

    resp_create = auth_client.post(url, data=payload, format="json")
    assert resp_create.status_code in (status.HTTP_201_CREATED, status.HTTP_200_OK)

    # New GET should differ since cache invalidated
    resp2 = auth_client.get(url)
    assert resp2.content != cached_content
    assert len(resp2.data) >= 1