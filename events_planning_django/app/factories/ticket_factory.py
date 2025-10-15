from . import BaseFactory, faker
from app.models import Ticket


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
