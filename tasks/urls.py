from django.urls import path

from .views import TaskCompleteView, TaskCreateView, TaskDeleteView, TaskDetailView, TaskListView, TaskUpdateView

app_name = "tasks"

urlpatterns = [
    path("", TaskListView.as_view(), name="list"),
    path("new/", TaskCreateView.as_view(), name="create"),
    path("<int:pk>/", TaskDetailView.as_view(), name="detail"),
    path("<int:pk>/edit/", TaskUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", TaskDeleteView.as_view(), name="delete"),
    path("<int:pk>/complete/", TaskCompleteView.as_view(), name="complete"),
]
