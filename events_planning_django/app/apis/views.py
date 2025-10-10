from rest_framework import views, generics
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from django.contrib.auth import authenticate, login, logout
from rest_framework.authentication import TokenAuthentication
from app.models import CustomUser, Event, Ticket
from .filters import TicketFilter , EventFilter
from . import permissions as custom_permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    EventSerializer,
    TicketSerializer,
)
from .pagination import EventPagination


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
    pagination_class = EventPagination
    filter_backends = [SearchFilter , DjangoFilterBackend]
    filterset_class = EventFilter
    search_fields = ["title", "organiser__username"]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, custom_permissions.IsOrganiser]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        serializer.save(organiser=self.request.user)

    @action(
        detail=False, methods=["get"], url_path="organiser/(?P<organiser_id>[^/.]+)"
    )
    def by_organiser(self, request, organiser_id=None):
        """Return all events by a specific organiser."""
        events = Event.objects.filter(organiser__id=organiser_id)
        page = self.paginate_queryset(events)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)


class TicketListView(generics.ListAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, custom_permissions.IsOrganiser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = TicketFilter
    search_fields = ["ticket_code", "event__title", "attendee__username"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and user.user_type == "organiser":
            return queryset.filter(event__organiser=user)
        return queryset
