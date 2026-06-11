from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from analytics.models import ActivityLog
from notifications.models import Notification

from .forms import TaskForm
from .models import Task


class TaskQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        user = self.request.user
        return Task.objects.filter(
            Q(assignee=user) | Q(reporter=user) | Q(project__owner=user) | Q(project__members=user)
        ).distinct()


class TaskListView(TaskQuerysetMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "").strip()
        status = self.request.GET.get("status", "").strip()
        priority = self.request.GET.get("priority", "").strip()
        due = self.request.GET.get("due", "").strip()
        today = Task.today()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) | Q(description__icontains=query) | Q(project__name__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if due == "overdue":
            queryset = queryset.filter(due_date__lt=today).exclude(status="done")
        elif due == "today":
            queryset = queryset.filter(due_date=today)
        elif due == "upcoming":
            queryset = queryset.filter(due_date__gt=today)
        elif due == "no_due":
            queryset = queryset.filter(due_date__isnull=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_choices"] = Task.STATUS_CHOICES
        context["priority_choices"] = Task.PRIORITY_CHOICES
        context["due_filters"] = [
            ("overdue", "Overdue"),
            ("today", "Due today"),
            ("upcoming", "Upcoming"),
            ("no_due", "No due date"),
        ]
        context["filters"] = {
            "q": self.request.GET.get("q", ""),
            "status": self.request.GET.get("status", ""),
            "priority": self.request.GET.get("priority", ""),
            "due": self.request.GET.get("due", ""),
        }
        return context


class TaskDetailView(TaskQuerysetMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        response = super().form_valid(form)
        self._create_assignment_notification()
        ActivityLog.objects.create(
            actor=self.request.user,
            action="created",
            object_type="task",
            object_id=self.object.pk,
            metadata={"object_name": self.object.title, "message": f"Created task {self.object.title}"},
        )
        messages.success(self.request, "Task created successfully.")
        return response

    def _create_assignment_notification(self):
        if self.object.assignee and self.object.assignee != self.request.user:
            Notification.objects.create(
                recipient=self.object.assignee,
                title="New task assigned",
                message=f"You were assigned to {self.object.title}.",
                level="info",
                link=self.object.get_absolute_url(),
            )


class TaskUpdateView(TaskQuerysetMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        old_assignee_id = self.get_queryset().get(pk=self.object.pk).assignee_id
        response = super().form_valid(form)
        if self.object.assignee_id and self.object.assignee_id != old_assignee_id:
            Notification.objects.create(
                recipient=self.object.assignee,
                title="Task assigned",
                message=f"You were assigned to {self.object.title}.",
                level="info",
                link=self.object.get_absolute_url(),
            )
        ActivityLog.objects.create(
            actor=self.request.user,
            action="updated",
            object_type="task",
            object_id=self.object.pk,
            metadata={"object_name": self.object.title, "message": f"Updated task {self.object.title}"},
        )
        messages.success(self.request, "Task updated successfully.")
        return response

    def get_success_url(self):
        return reverse_lazy("tasks:detail", kwargs={"pk": self.object.pk})


class TaskDeleteView(TaskQuerysetMixin, DeleteView):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("tasks:list")

    def form_valid(self, form):
        task_name = self.object.title
        task_id = self.object.pk
        response = super().form_valid(form)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="deleted",
            object_type="task",
            object_id=task_id,
            metadata={"object_name": task_name, "message": f"Deleted task {task_name}"},
        )
        messages.success(self.request, "Task deleted successfully.")
        return response


class TaskCompleteView(TaskQuerysetMixin, View):
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        task.status = "done"
        task.completed_at = timezone.now()
        task.save(update_fields=["status", "completed_at", "updated_at"])
        ActivityLog.objects.create(
            actor=request.user,
            action="completed",
            object_type="task",
            object_id=task.pk,
            metadata={"object_name": task.title, "message": f"Completed task {task.title}"},
        )
        messages.success(request, "Task marked as completed.")
        return redirect(task.get_absolute_url())
