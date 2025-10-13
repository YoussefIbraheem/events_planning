from .models import CustomUser, Event, Order
from faker import Faker
from abc import ABC, abstractmethod
import datetime
import json

factory_faker = Faker()


class AbstractFactory(ABC):
    @staticmethod
    @abstractmethod
    def create(**kwargs):
        pass


class UserFactory(AbstractFactory):

    @staticmethod
    def create(**kwargs):

        return {
            "username": kwargs.get("username", factory_faker.unique.user_name()),
            "email": kwargs.get("email", factory_faker.unique.email()),
            "password": kwargs.get("password", "password@123"),
            "first_name": kwargs.get("first_name", factory_faker.first_name()),
            "last_name": kwargs.get("last_name", factory_faker.last_name()),
            "user_type": kwargs.get(
                "user_type",
                factory_faker.random_element(list(CustomUser.UserType.values)),
            ),
        }


class EventFactory(AbstractFactory):

    @staticmethod
    def create(**kwargs):
        tomorrow_datetime = datetime.date.today() + datetime.timedelta(days=1)
        return {
            "title": kwargs.get("title", factory_faker.word()),
            "description": kwargs.get("description", factory_faker.paragraph(10)),
            "coordinates": kwargs.get(
                "coordinates",
                json.dumps(
                    {
                        "lat": str(factory_faker.latitude()),
                        "lng": str(factory_faker.longitude()),
                    },
                    separators=(",", ":"),
                ),
            ),
            "date_time": kwargs.get(
                "date_time",
                factory_faker.date_time_between_dates(
                    tomorrow_datetime, tomorrow_datetime + datetime.timedelta(days=30)
                ),
            ),
            "tickets_amount": kwargs.get(
                "tickets_amount", factory_faker.random_int(50, 500)
            ),
            "ticket_price": kwargs.get(
                "ticket_price", round(factory_faker.pyfloat(2, 2, positive=True), 2)
            ),
            "organiser": kwargs.get(
                "organiser", None
            ),  # Should be set to a valid organiser user instance
        }


class TicketFactory(AbstractFactory):

    @staticmethod
    def create(**kwargs):
        return {
            "ticket_code": kwargs.get("ticket_code", factory_faker.unique.uuid4()),
            "event": kwargs.get(
                "event", None
            ),  # Should be set to a valid event instance
            "attendee": kwargs.get(
                "attendee", None
            ),  # Should be set to a valid attendee user instance
            "ticket_price": kwargs.get("ticket_price", 0),
        }


class OrderFactory(AbstractFactory):

    @staticmethod
    def create(**kwargs):
        return {
            "total_price": kwargs.get("total_price", 0),
            "payment_method": kwargs.get(
                "payment_method",
                factory_faker.random_element(list(Order.PaymentMethod.values)),
            ),
            "status": kwargs.get(
                "status", factory_faker.random_element(list(Order.Status.values))
            ),
            "attendee": kwargs.get("attendee", None),
        }


class OrderItemFactory(AbstractFactory):

    @staticmethod
    def create(**kwargs):
        return {
            "order": kwargs.get("order", None),
            "event": kwargs.get("event", None),
            "ticket_price": kwargs.get("ticket_price", 0),
            "quantity": kwargs.get("quantity", 0),
        }
