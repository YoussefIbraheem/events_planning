from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError , NotFound
from app.models import CustomUser, Event
from .validators import UserLoginValidator, UserRegisterValidator, EventValidator


class AuthUtils:

    def login(self, request):

        validated_data = UserLoginValidator.validate(request.data)
        username = validated_data.get("username")
        password = validated_data.get("password")
        user = authenticate(request, username=username, password=password)
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return user, token

    def register(self, request):
        validated_data = UserRegisterValidator.validate(request.data)
        username = validated_data.get("username")
        email = validated_data.get("email")
        password = validated_data.get("password")
        user = CustomUser.objects.create_user(
            username=username, email=email, password=password
        )
        token, _ = Token.objects.get_or_create(user=user)
        login(request, user)
        return user, token

    def logout(self, request):
        logout(request)
        return True


class EventUtils:

    def list_events(self):

        events = Event.objects.all()
        return events

    def retrieve_event(self, pk):
        event = Event.objects.filter(pk=pk).first()
        if not event:
            raise NotFound("Event not found", code=404)
        return event

    def create_event(self, organiser, **kwargs):
        validated_data = EventValidator.validate(kwargs)
        if not organiser or organiser.user_type != CustomUser.UserType.ORGANISER:
            raise ValueError("Only organisers can create events")
        event = Event.objects.create(organiser=organiser, **validated_data)
        event.save()
        return event

    def update_event(self, pk, **kwargs):
        event = Event.objects.get_or_404(pk=pk)
        validated_data = EventValidator.validate(kwargs)
        for key, value in validated_data.items():
            setattr(event, key, value)
        event.save()
        return event

    def delete_event(self, pk):
        event = Event.objects.get_or_404(pk=pk)
        event.delete()
        return True
