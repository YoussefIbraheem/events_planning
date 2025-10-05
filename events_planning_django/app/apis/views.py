from rest_framework import views
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import authenticate, login, logout
from rest_framework.authentication import TokenAuthentication
from app.models import CustomUser, Event, Ticket
from . import permissions as custom_permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    EventSerializer,
    TicketSerializer,
)


class UserLoginView(views.APIView):


        
    @extend_schema(
        request=LoginSerializer,
        responses={200: UserSerializer, 401: "Unauthorized"},
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]
        user = authenticate(request, username=username, password=password)

        if not user:
            raise AuthenticationFailed("Invalid credentials")

        token, _ = Token.objects.get_or_create(user=user)

        login(request, user)

        return Response(
            {"user": UserSerializer(user).data, "access_token": token.key},
            status=status.HTTP_200_OK,
        )


class UserRegisterView(views.APIView):

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserSerializer, 400: "Bad Request"},
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.create(serializer.validated_data)
        token, _ = Token.objects.get_or_create(user=user)

        login(request, user)

        return Response(
            {"user": UserSerializer(user).data, "access_token": token.key},
            status=status.HTTP_201_CREATED,
        )


class UserLogoutView(views.APIView):

    @extend_schema(responses={200: "Logged out successfully"})
    def post(self, request):

        logout(request)

        return Response(
            {"detail": "Logged out successfully"}, status=status.HTTP_200_OK
        )


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, custom_permissions.IsOrganiser]

    def perform_create(self, serializer):
        print(self.request.user)
        serializer.save(organiser=self.request.user)


class TicketListView(views.APIView):
    permission_classes = [IsAuthenticatedOrReadOnly, custom_permissions.IsOrganiser]

    # Swagger documentation for filtering parameters
    @extend_schema(
        responses={200: "List of tickets", 403: "Forbidden", 404: "Not Found"},
        parameters=[
            OpenApiParameter(
                name="date_from",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter tickets for events occurring on or after this date.",
            ),
            OpenApiParameter(
                name="date_to",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter tickets for events occurring on or before this date.",
            ),
            OpenApiParameter(
                name="event_id",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Filter tickets for a specific event by its ID.",
            ),
        ],
    )
    def get(self, request):
        date_from = request.query_params.get("date_from", None)
        date_to = request.query_params.get("date_to", None)
        event_id = request.query_params.get("event_id", None)

        query = Ticket.objects
        if event_id:
            query = query.filter(event__id=event_id)
        if date_from:
            query = query.filter(event__date_time__gte=date_from)
        if date_to:
            query = query.filter(event__date_time__lte=date_to)

        tickets = query.all()
        serializer = TicketSerializer(tickets, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
