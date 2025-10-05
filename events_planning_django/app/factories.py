from .models import CustomUser, Event
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
            "location_type": kwargs.get(
                "location_type", Event.EventType.GENERAL_ADMISSION # TODO figure how to handle seated events
            ),
            "date_time": kwargs.get(
                "date_time",
                factory_faker.date_time_between_dates(
                    tomorrow_datetime, tomorrow_datetime + datetime.timedelta(days=30)
                ),
            ),
            "tickets_available": kwargs.get(
                "tickets_available", factory_faker.random_int(50, 500)
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
            "seat_number": kwargs.get(
                "seat_number", str(factory_faker.random_int(1, 1000))
            ),
            "event": kwargs.get(
                "event", None
            ),  # Should be set to a valid event instance
            "attendee": kwargs.get(
                "attendee", None
            ),  # Should be set to a valid attendee user instance
        }
