from django.urls import path

from .views import (
    TaskCalendarView,
    TaskCompleteView,
    TaskCreateView,
    TaskDeleteView,
    TaskDetailView,
    TaskKanbanView,
    TaskListView,
    TaskStatusUpdateView,
    TaskUpdateView,
)

app_name = "tasks"

urlpatterns = [
    path("", TaskListView.as_view(), name="list"),
    path("kanban/", TaskKanbanView.as_view(), name="kanban"),
    path("calendar/", TaskCalendarView.as_view(), name="calendar"),
    path("new/", TaskCreateView.as_view(), name="create"),
    path("<int:pk>/status/", TaskStatusUpdateView.as_view(), name="update_status"),
    path("<int:pk>/", TaskDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", TaskUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", TaskDeleteView.as_view(), name="delete"),
    path("<int:pk>/complete/", TaskCompleteView.as_view(), name="complete"),
]
