from django.urls import path, include
from .views import (
    UserLoginView,
    UserRegisterView,
    UserLogoutView,
    EventViewSet,
    TicketListView,
    OrderViewSet,
    OrganiserDashboardView
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.routers import SimpleRouter

router = SimpleRouter()
router.register(r"events", EventViewSet, basename="event")
router.register(r"orders",OrderViewSet, basename="order")

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("register/", UserRegisterView.as_view(), name="register"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("tickets/", TicketListView.as_view(), name="tickets"),
    path("stats/",OrganiserDashboardView.as_view(),name="stats"),
    path("", include(router.urls)),
    # schemas and docs URLs
    path("schema/", SpectacularAPIView.as_view(api_version="v2"), name="schema"),
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
]
