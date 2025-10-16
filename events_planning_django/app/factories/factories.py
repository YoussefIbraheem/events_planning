from . import BaseFactory, faker
import json
import datetime
from app.models import Event, Ticket, Order, OrderItem, CustomUser


class EventFactory(BaseFactory):

    model = Event

    def _get_defaults(self, **kwargs):
        tomorrow_datetime = datetime.date.today() + datetime.timedelta(days=1)
        return {
            "title": kwargs.get("title", faker.word()),
            "description": kwargs.get("description", faker.paragraph(10)),
            "coordinates": kwargs.get(
                "coordinates",
                json.dumps(
                    {
                        "lat": str(faker.latitude()),
                        "lng": str(faker.longitude()),
                    },
                    separators=(",", ":"),
                ),
            ),
            "date_time": kwargs.get(
                "date_time",
                faker.date_time_between_dates(
                    tomorrow_datetime, tomorrow_datetime + datetime.timedelta(days=30)
                ),
            ),
            "event_status": kwargs.get(
                "event_status", faker.random_element(list(Event.Status.values))
            ),
            "tickets_amount": kwargs.get("tickets_amount", faker.random_int(50, 500)),
            "ticket_price": kwargs.get(
                "ticket_price", round(faker.pyfloat(2, 2, positive=True), 2)
            ),
            "organiser": kwargs.get(
                "organiser", None
            ),  # Should be set to a valid organiser user instance
        }


class OrderFactory(BaseFactory):

    model = Order

    def _get_defaults(self, **kwargs):
        return {
            "total_price": kwargs.get("total_price", 0),
            "payment_method": kwargs.get(
                "payment_method",
                faker.random_element(list(Order.PaymentMethod.values)),
            ),
            "order_status": kwargs.get(
                "order_status", faker.random_element(list(Order.Status.values))
            ),
            "attendee": kwargs.get("attendee", None),
        }


class OrderItemFactory(BaseFactory):

    model = OrderItem

    def _get_defaults(self, **kwargs):
        return {
            "order": kwargs.get("order", None),
            "event": kwargs.get("event", None),
            "ticket_price": kwargs.get("ticket_price", 0),
            "quantity": kwargs.get("quantity", faker.pyint(1, 3)),
        }


class TicketFactory(BaseFactory):

    model = Ticket

    def _get_defaults(self, **kwargs):
        return {
            "ticket_code": kwargs.get("ticket_code", faker.unique.uuid4()),
            "event": kwargs.get(
                "event", None
            ),  # Should be set to a valid event instance
            "attendee": kwargs.get(
                "attendee", None
            ),  # Should be set to a valid attendee user instance
            # "ticket_price": kwargs.get("ticket_price", 0),
        }


class UserFactory(BaseFactory):

    model = CustomUser

    def _get_defaults(self, **kwargs):

        return {
            "username": kwargs.get("username", faker.unique.user_name()),
            "email": kwargs.get("email", faker.unique.email()),
            "password": kwargs.get("password", "password@123"),
            "first_name": kwargs.get("first_name", faker.first_name()),
            "last_name": kwargs.get("last_name", faker.last_name()),
            "user_type": kwargs.get(
                "user_type",
                faker.random_element(list(CustomUser.UserType.values)),
            ),
        }
