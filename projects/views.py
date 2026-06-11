from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from analytics.models import ActivityLog

from .forms import ProjectForm
from .models import Project


class ProjectQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        user = self.request.user
        return Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()


class ProjectOwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        obj = self.get_object()
        return obj.owner == self.request.user


class ProjectListView(ProjectQuerysetMixin, ListView):
    model = Project
    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        priority = self.request.GET.get("priority", "").strip()

        if query:
            queryset = queryset.filter(Q(name__icontains=query) | Q(description__icontains=query))
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Project.STATUS_CHOICES
        context["priority_choices"] = Project.PRIORITY_CHOICES
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "priority": self.request.GET.get("priority", ""),
        }
        return context


class ProjectDetailView(ProjectQuerysetMixin, DetailView):
    model = Project
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project_tasks"] = self.object.tasks.select_related("assignee").order_by("status", "due_date")[:12]
        context["project_activity"] = ActivityLog.objects.filter(
            object_type="project",
            object_id=self.object.pk,
        )[:8]
        return context


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user
        response = super().form_valid(form)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="created",
            object_type="project",
            object_id=self.object.pk,
            metadata={"object_name": self.object.name, "message": f"Created project {self.object.name}"},
        )
        messages.success(self.request, "Project created successfully.")
        return response


class ProjectUpdateView(ProjectQuerysetMixin, ProjectOwnerRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/project_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="updated",
            object_type="project",
            object_id=self.object.pk,
            metadata={"object_name": self.object.name, "message": f"Updated project {self.object.name}"},
        )
        messages.success(self.request, "Project updated successfully.")
        return response

    def get_success_url(self):
        return reverse_lazy("projects:detail", kwargs={"slug": self.object.slug})


class ProjectDeleteView(ProjectQuerysetMixin, ProjectOwnerRequiredMixin, DeleteView):
    model = Project
    template_name = "projects/project_confirm_delete.html"
    success_url = reverse_lazy("projects:list")

    def form_valid(self, form):
        project_name = self.object.name
        project_id = self.object.pk
        response = super().form_valid(form)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="deleted",
            object_type="project",
            object_id=project_id,
            metadata={"object_name": project_name, "message": f"Deleted project {project_name}"},
        )
        messages.success(self.request, "Project deleted successfully.")
        return response
