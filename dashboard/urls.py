from django.urls import path

from .views import HomeDashboardView

app_name = "dashboard"

urlpatterns = [
    path("", HomeDashboardView.as_view(), name="home"),
]
