
from django.urls import path , include
from .views import UserLoginView, UserRegisterView, UserLogoutView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import SimpleRouter
from .views import EventViewSet

router = SimpleRouter()
router.register(r'events', EventViewSet, basename='event')


urlpatterns = [
    path('login/', UserLoginView.as_view(), name='login'),
    path('register/', UserRegisterView.as_view(), name='register'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('', include(router.urls)),
    # schemas and docs URLs
    path('schema/', SpectacularAPIView.as_view(api_version='v2'), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]


