from django.urls import path

from .views import ArchitectureView, HomeDashboardView

app_name = "dashboard"

urlpatterns = [
    path("", HomeDashboardView.as_view(), name="home"),
    path("architecture/", ArchitectureView.as_view(), name="architecture"),
]
