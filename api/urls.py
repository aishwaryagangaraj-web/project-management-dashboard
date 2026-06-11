from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import AnalyticsStatsAPIView, NotificationViewSet, ProfileAPIView, ProjectViewSet, RegisterAPIView, TaskViewSet

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="api-projects")
router.register(r"tasks", TaskViewSet, basename="api-tasks")
router.register(r"notifications", NotificationViewSet, basename="api-notifications")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/login/", TokenObtainPairView.as_view(), name="api-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="api-refresh"),
    path("auth/register/", RegisterAPIView.as_view(), name="api-register"),
    path("auth/profile/", ProfileAPIView.as_view(), name="api-profile"),
    path("analytics/stats/", AnalyticsStatsAPIView.as_view(), name="api-analytics"),
    path("schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
]
