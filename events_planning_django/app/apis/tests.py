from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from app.models import CustomUser, Event
from django.utils import timezone
from rest_framework.authtoken.models import Token
import datetime


class UserAuthTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")
        self.user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
            "password2": "password123",
        }
        self.user = CustomUser.objects.create_user(
            username="organiser",
            email="organiser@example.com",
            password="password123",
            user_type=CustomUser.UserType.ORGANISER,
        )
        self.token = Token.objects.create(user=self.user)

    def test_register_user_success(self):
        response = self.client.post(self.register_url, self.user_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access_token", response.data)

    def test_register_user_password_mismatch(self):
        bad_data = self.user_data.copy()
        bad_data["password2"] = "wrongpassword"
        response = self.client.post(self.register_url, bad_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {"username": "organiser", "password": "password123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data)

    def test_login_failure(self):
        response = self.client.post(
            self.login_url,
            {"username": "organiser", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_success(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.token.key)
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class EventTests(APITestCase):
    def setUp(self):
        self.organiser = CustomUser.objects.create_user(
            username="eventorganiser",
            email="org@example.com",
            password="password123",
            user_type=CustomUser.UserType.ORGANISER,
        )
        self.attendee = CustomUser.objects.create_user(
            username="attendee",
            email="attendee@example.com",
            password="password123",
            user_type=CustomUser.UserType.ATTENDEE,
        )
        self.organiser_token = Token.objects.create(user=self.organiser)
        self.attendee_token = Token.objects.create(user=self.attendee)
        self.event_url = reverse("event-list")  # DRF router registered name

    def test_event_creation_by_organiser(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.organiser_token.key)
        payload = {
            "title": "Music Concert",
            "description": "An amazing concert.",
            "coordinates": {"lat": 30.0444, "lng": 31.2357},
            "date_time": (timezone.now() + datetime.timedelta(days=1)).isoformat(),
            "tickets_available": 100,
            "ticket_price": 50.0,
        }
        response = self.client.post(self.event_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Music Concert")

    def test_event_creation_by_attendee_forbidden(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.attendee_token.key)
        payload = {
            "title": "Unauthorized Event",
            "description": "Should fail.",
            "coordinates": {"lat": 40.7128, "lng": -74.0060},
            "date_time": (timezone.now() + datetime.timedelta(days=2)).isoformat(),
            "tickets_available": 50,
            "ticket_price": 25.0,
        }
        response = self.client.post(self.event_url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_event_list_public_access(self):
        # Anyone can GET event list
        response = self.client.get(self.event_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_event_update_by_organiser(self):
        # Create event
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.organiser_token.key)
        event = Event.objects.create(
            title="Old Title",
            description="desc",
            coordinates={"lat": 10.0, "lng": 10.0},
            date_time=timezone.now() + datetime.timedelta(days=3),
            tickets_available=10,
            ticket_price=100.0,
            organiser=self.organiser,
        )
        url = reverse("event-detail", args=[event.id])
        response = self.client.patch(url, {"title": "New Title"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], "New Title")

    def test_event_delete_by_non_organiser(self):
        event = Event.objects.create(
            title="Concert",
            description="desc",
            coordinates={"lat": 10.0, "lng": 10.0},
            date_time=timezone.now() + datetime.timedelta(days=3),
            tickets_available=10,
            ticket_price=100.0,
            organiser=self.organiser,
        )
        url = reverse("event-detail", args=[event.id])
        self.client.credentials(HTTP_AUTHORIZATION="Token " + self.attendee_token.key)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)