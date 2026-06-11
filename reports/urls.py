from django.urls import path

from .views import AnalyticsReportView, ProjectReportView, TaskReportView

app_name = "reports"

urlpatterns = [
    path("analytics/", AnalyticsReportView.as_view(), name="analytics"),
    path("projects/<slug:slug>/", ProjectReportView.as_view(), name="project"),
    path("tasks/<int:pk>/", TaskReportView.as_view(), name="task"),
]
