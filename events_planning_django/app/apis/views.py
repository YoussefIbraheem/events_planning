from rest_framework.views import APIView
from rest_framework import viewsets, status, permissions
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema
from django.contrib.auth import authenticate, login, logout

from app.models import CustomUser, Event
from . import permissions as custom_permissions
from .serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    EventSerializer,
)


class UserLoginView(APIView):

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


class UserRegisterView(APIView):

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


class UserLogoutView(APIView):

    @extend_schema(responses={200: "Logged out successfully"})
    def post(self, request):

        logout(request)

        return Response(
            {"detail": "Logged out successfully"}, status=status.HTTP_200_OK
        )


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            self.permission_classes = [custom_permissions.IsOrganiser]
        else:
            self.permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(organiser=self.request.user)
