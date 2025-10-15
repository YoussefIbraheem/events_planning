from . import BaseFactory, faker
import json
import datetime
from app.models import Event


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
