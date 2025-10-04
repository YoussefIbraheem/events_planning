from rest_framework.views import APIView
from rest_framework.decorators import action, permission_classes
from rest_framework import viewsets
from . import permissions as custom_permissions
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.exceptions import APIException, AuthenticationFailed
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, extend_schema_view
from .utils import AuthUtils, EventUtils
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    EventSerializer,
    CreateEventSerializer,
)


class UserLoginView(APIView):

    @extend_schema(
        request=LoginSerializer, responses={200: UserSerializer, 401: "Unauthorized"}
    )
    def post(self, request):
        auth_utils = AuthUtils()
        try:
            user, token = auth_utils.login(request)
            user_data = UserSerializer(user).data
            return Response({"user": user_data, "access_token": token.key}, status=200)
        except Exception as e:
            raise AuthenticationFailed(str(e))


class UserRegisterView(APIView):
    @extend_schema(
        request=RegisterSerializer, responses={201: UserSerializer, 400: "Bad Request"}
    )
    def post(self, request):
        auth_utils = AuthUtils()
        try:
            user, token = auth_utils.register(request)
            user_data = UserSerializer(user).data
            return Response({"user": user_data, "access_token": token.key}, status=200)
        except Exception as e:
            raise APIException(str(e))


class UserLogoutView(APIView):
    @extend_schema(responses={200: "Logged out successfully"})
    def post(self, request):
        auth_utils = AuthUtils()
        auth_utils.logout(request)
        return Response({"detail": "Logged out successfully"}, status=200)


class EventViewSet(viewsets.ViewSet):
    """
    A simple ViewSet for listing or retrieving events.
    """

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly, custom_permissions.IsOrganiser]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]

        return [permission() for permission in permission_classes]

    @extend_schema(responses={200: EventSerializer(many=True)})
    def list(self, request):
        try:
            event_utils = EventUtils()
            events = event_utils.list_events()
            serialized_events = EventSerializer(events, many=True)
            return Response(serialized_events.data, status=200)
        except Exception as e:
            raise APIException(str(e))

    @extend_schema(responses={200: EventSerializer()})
    def retrieve(self, request, pk=None):
        try:
            event_utils = EventUtils()
            event = event_utils.retrieve_event(pk)
            serialized_event = EventSerializer(event)
            return Response(serialized_event.data, status=200)
        except Exception as e:
            raise APIException(str(e))

    @extend_schema(request=CreateEventSerializer, responses={201: EventSerializer()})
    def create(self, request):
        try:
            organiser = request.user
            event_utils = EventUtils()
            event = event_utils.create_event(organiser, **request.data)
            serialized_event = EventSerializer(event)
            return Response(serialized_event.data, status=201)
        except Exception as e:
            raise APIException(str(e))

    @extend_schema(request=CreateEventSerializer, responses={200: EventSerializer()})
    def update(self, request, pk=None):
        try:
            event_utils = EventUtils()
            event = event_utils.update_event(pk, **request.data)
            serialized_event = EventSerializer(event)
            return Response(serialized_event.data, status=200)
        except Exception as e:
            raise APIException(str(e))

    @extend_schema(responses={204: "No Content"})
    def destroy(self, request, pk=None):
        try:
            event_utils = EventUtils()
            event_utils.delete_event(pk)
            return Response(status=204)
        except Exception as e:
            raise APIException(str(e))
