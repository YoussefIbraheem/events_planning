from . import BaseFactory, faker
from app.models import OrderItem


class OrderItemFactory(BaseFactory):

    model = OrderItem

    def _get_defaults(self, **kwargs):
        return {
            "order": kwargs.get("order", None),
            "event": kwargs.get("event", None),
            "ticket_price": kwargs.get("ticket_price", 0),
            "quantity": kwargs.get("quantity", faker.pyint(1,3)),
        }
