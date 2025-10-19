from rest_framework import views, generics
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.filters import SearchFilter
from rest_framework.exceptions import (
    AuthenticationFailed,
    APIException,
    ValidationError,
    NotAuthenticated,
)
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from django.contrib.auth import authenticate, login, logout
from app.models import CustomUser, Event, Ticket, Order, OrderItem
from .filters import TicketFilter, EventFilter, OrderFilter
from . import permissions as custom_permissions
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    EventSerializer,
    TicketSerializer,
    OrderSerializer,
    CreateOrderSerializer,
)
from app.services.orders import OrderService
from app.services.tickets import TicketService
from .pagination import EventPagination
import logging


class UserLoginView(views.APIView):

    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Unauthorized"),
        },
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

    serializer_class = RegisterSerializer

    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: UserSerializer,
            400: OpenApiResponse(description="Bad Request"),
        },
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

    serializer_class = LoginSerializer

    @extend_schema(
        responses={200: OpenApiResponse(description="Logged out successfully")}
    )
    def post(self, request):

        logout(request)

        return Response(
            {"detail": "Logged out successfully"}, status=status.HTTP_200_OK
        )


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    pagination_class = EventPagination
    filter_backends = [SearchFilter, DjangoFilterBackend]
    filterset_class = EventFilter
    search_fields = ["title", "organiser__username"]

    @method_decorator(cache_page(60 * 60 * 2, key_prefix="list-events"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

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

    @method_decorator(cache_page(60 * 60 * 2, key_prefix="list-tickets"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, custom_permissions.IsAttendee]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @method_decorator(cache_page(60 * 60 * 2, key_prefix="list-orders"))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return CreateOrderSerializer
        return OrderSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type == CustomUser.UserType.ATTENDEE:
            return (
                Order.objects.filter(attendee=user)
                .select_related("attendee")
                .prefetch_related("items__event")
            )
        else:
            return super().get_queryset()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        order = OrderService.create_order(request.user, serializer.validated_data)

        read_serializer = OrderSerializer(order, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)


    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)

        updated_order = OrderService.update_order(
            user=request.user,
            order=instance,
            new_validated_data=serializer.validated_data,
        )

        read_serializer = OrderSerializer(updated_order, context={"request": request})
        return Response(read_serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        if instance.order_status not in [
            Order.Status.CANCELLED or Order.Status.EXPIRED
        ]:
            raise NotAuthenticated(
                "Order cannot be deleted. Please cancel the order or contact support.",
                status.HTTP_401_UNAUTHORIZED,
            )
        return super().perform_destroy(instance)

    # * -------------------#
    # * CUSTOM ACTIONS
    # * -------------------#

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Tickets reserved successfully."),
            400: OpenApiResponse(description="Reservation failed."),
        }
    )
    @action(
        detail=True, methods=["POST"], url_path="checkout", url_name="order_checkout"
    )
    def checkout(self, request, pk=None):

        order = self.get_object()

        try:
            TicketService.reserve_tickets(order)
            return Response(
                {"detail": "Tickets Reserved Successfully"}, status=status.HTTP_200_OK
            )
        except ValueError as e:
            raise ValidationError({"detail": str(e)}, code=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Tickets reserved successfully."),
            400: OpenApiResponse(description="Reservation failed."),
        }
    )
    @action(
        detail=True, methods=["POST"], url_path="finalise", url_name="order_finalize"
    )
    def finalize(self, request, pk=None):
        order = self.get_object()
        try:
            TicketService.finalize_order(order)
            return Response(
                {"detail": "Tickets Reserved Successfully."}, status=status.HTTP_200_OK
            )
        except ValueError as e:
            raise ValidationError({"detail": str(e)}, code=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        responses={
            200: OpenApiResponse(description="Order cancelled successfully."),
            400: OpenApiResponse(description="Cancellation failed."),
        }
    )
    @action(detail=True, methods=["POST"], url_path="cancel", url_name="order_cancel")
    def cancel(self, request, pk=None):
        order = self.get_object()
        try:
            TicketService.release_reservation(order)
            return Response(
                {"detail": "Order cancelled successfully."}, status=status.HTTP_200_OK
            )
        except ValueError as e:
            raise ValidationError({"detail": str(e)}, code=status.HTTP_400_BAD_REQUEST)
