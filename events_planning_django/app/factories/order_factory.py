from . import BaseFactory, faker
from app.models import Order


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
