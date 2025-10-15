from . import BaseFactory, faker
from app.models import CustomUser


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
