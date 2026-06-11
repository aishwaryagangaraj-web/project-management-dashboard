from django.urls import path

from .views import ProjectCreateView, ProjectDeleteView, ProjectDetailView, ProjectListView, ProjectUpdateView

app_name = "projects"

urlpatterns = [
    path("", ProjectListView.as_view(), name="list"),
    path("new/", ProjectCreateView.as_view(), name="create"),
    path("<slug:slug>/", ProjectDetailView.as_view(), name="detail"),
    path("<slug:slug>/edit/", ProjectUpdateView.as_view(), name="update"),
    path("<slug:slug>/delete/", ProjectDeleteView.as_view(), name="delete"),
]
