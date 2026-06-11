import calendar
import json
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from accounts.access import can_create_task, can_edit_task_details, can_manage_task_content, can_update_task_status, visible_tasks_queryset
from analytics.models import ActivityLog
from .forms import TaskCommentForm, TaskForm
from .models import Task, TaskComment, validate_task_attachment


def can_manage_task(user, task):
    return can_edit_task_details(user, task)


def can_manage_comment(user, comment):
    return user == comment.user or can_manage_task_content(user, comment.task)


def delete_uploaded_file(file_field):
    if not file_field:
        return
    storage = file_field.storage
    if storage.exists(file_field.name):
        storage.delete(file_field.name)


class TaskQuerysetMixin(LoginRequiredMixin):
    def get_queryset(self):
        return visible_tasks_queryset(
            self.request.user,
            Task.objects.select_related("project", "assignee", "reporter", "project__owner"),
        ).annotate(comment_count=Count("comments", distinct=True))


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
        context["can_create_task"] = can_create_task(self.request.user)
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


class TaskKanbanView(TaskQuerysetMixin, ListView):
    model = Task
    template_name = "tasks/task_kanban.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("project", "assignee")
            .order_by("due_date", "-priority", "-updated_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_task"] = can_create_task(self.request.user)
        columns = []
        for status, label in Task.STATUS_CHOICES:
            columns.append(
                {
                    "status": status,
                    "label": label,
                    "tasks": [task for task in context["tasks"] if task.status == status],
                }
            )
        context["kanban_columns"] = columns
        context["allowed_statuses"] = [status for status, _label in Task.STATUS_CHOICES]
        return context


class TaskCalendarView(TaskQuerysetMixin, ListView):
    model = Task
    template_name = "tasks/task_calendar.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .select_related("project", "assignee")
            .filter(due_date__isnull=False)
            .order_by("due_date", "status")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_task"] = can_create_task(self.request.user)
        today = timezone.localdate()
        year = self._get_int_param("year", today.year)
        month = self._get_int_param("month", today.month)
        try:
            current_month = date(year, month, 1)
        except ValueError:
            current_month = date(today.year, today.month, 1)

        _, last_day = calendar.monthrange(current_month.year, current_month.month)
        month_start = current_month
        month_end = date(current_month.year, current_month.month, last_day)
        tasks = list(self.get_queryset().filter(due_date__gte=month_start, due_date__lte=month_end))
        tasks_by_date = {}
        for task in tasks:
            tasks_by_date.setdefault(task.due_date, []).append(task)

        weeks = []
        for week in calendar.Calendar(firstweekday=0).monthdatescalendar(current_month.year, current_month.month):
            weeks.append(
                [
                    {
                        "date": day,
                        "in_month": day.month == current_month.month,
                        "is_today": day == today,
                        "tasks": tasks_by_date.get(day, []),
                    }
                    for day in week
                ]
            )

        previous_month = self._shift_month(current_month, -1)
        next_month = self._shift_month(current_month, 1)
        context.update(
            {
                "calendar_weeks": weeks,
                "current_month": current_month,
                "previous_month": previous_month,
                "next_month": next_month,
                "today": today,
            }
        )
        return context

    def _get_int_param(self, name, default):
        try:
            return int(self.request.GET.get(name, default))
        except (TypeError, ValueError):
            return default

    def _shift_month(self, value, offset):
        month = value.month + offset
        year = value.year
        if month < 1:
            month = 12
            year -= 1
        elif month > 12:
            month = 1
            year += 1
        return date(year, month, 1)


class TaskDetailView(TaskQuerysetMixin, DetailView):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_comments"] = (
            self.object.comments.select_related("user", "user__profile").all()
        )
        context["comment_form"] = TaskCommentForm()
        context["can_manage_task"] = can_edit_task_details(self.request.user, self.object)
        context["can_manage_task_content"] = can_manage_task_content(self.request.user, self.object)
        context["can_update_status"] = can_update_task_status(self.request.user, self.object)
        context["comment_count"] = getattr(self.object, "comment_count", self.object.comments.count())
        return context


class TaskCommentCreateView(TaskQuerysetMixin, View):
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        if not can_manage_task_content(request.user, task):
            messages.error(request, "You do not have permission to comment on this task.")
            return redirect(task.get_absolute_url())
        form = TaskCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.user = request.user
            comment.save()
            messages.success(request, "Comment added.")
        else:
            for error in form.errors.get("comment", []):
                messages.error(request, error)
        return redirect(task.get_absolute_url())


class TaskCommentUpdateView(TaskQuerysetMixin, UpdateView):
    model = TaskComment
    form_class = TaskCommentForm
    template_name = "tasks/task_comment_form.html"
    pk_url_kwarg = "comment_pk"

    def get_queryset(self):
        return TaskComment.objects.select_related("task", "task__project", "user").filter(task__in=super().get_queryset())

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_manage_comment(request.user, self.object):
            return redirect(self.object.task.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Comment updated.")
        return response

    def get_success_url(self):
        return self.object.task.get_absolute_url()


class TaskCommentDeleteView(TaskQuerysetMixin, View):
    def post(self, request, *args, **kwargs):
        comment = get_object_or_404(
            TaskComment.objects.select_related("task", "task__project", "user"),
            pk=kwargs["comment_pk"],
            task__in=self.get_queryset(),
        )
        if not can_manage_comment(request.user, comment):
            return redirect(comment.task.get_absolute_url())
        comment.delete()
        messages.success(request, "Comment deleted.")
        return redirect(comment.task.get_absolute_url())


class TaskAttachmentUploadView(TaskQuerysetMixin, View):
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        upload = request.FILES.get("attachment")
        if not upload:
            messages.error(request, "Choose a file to upload.")
            return redirect(task.get_absolute_url())
        if not can_manage_task_content(request.user, task):
            messages.error(request, "You do not have permission to upload files for this task.")
            return redirect(task.get_absolute_url())

        old_attachment = task.attachment
        try:
            validate_task_attachment(upload)
            task.attachment.save(upload.name, upload, save=False)
            task.save()
        except ValidationError as exc:
            if task.attachment and task.attachment.name != getattr(old_attachment, "name", None):
                delete_uploaded_file(task.attachment)
            task.attachment = old_attachment
            messages.error(request, " ".join(sum(exc.message_dict.values(), [])) if hasattr(exc, "message_dict") else str(exc))
            return redirect(task.get_absolute_url())

        if old_attachment and old_attachment.name != task.attachment.name:
            delete_uploaded_file(old_attachment)
        messages.success(request, "Attachment uploaded.")
        return redirect(task.get_absolute_url())


class TaskAttachmentDeleteView(TaskQuerysetMixin, View):
    def post(self, request, *args, **kwargs):
        task = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        if not can_manage_task_content(request.user, task):
            messages.error(request, "You do not have permission to remove files for this task.")
            return redirect(task.get_absolute_url())
        if task.attachment:
            delete_uploaded_file(task.attachment)
            task.attachment = None
            task.save(update_fields=["attachment", "updated_at"])
            messages.success(request, "Attachment removed.")
        return redirect(task.get_absolute_url())


class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        if not can_create_task(request.user):
            messages.error(request, "You do not have permission to create tasks.")
            return redirect("dashboard:home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.reporter = self.request.user
        response = super().form_valid(form)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="created",
            object_type="task",
            object_id=self.object.pk,
            metadata={"object_name": self.object.title, "message": f"Created task {self.object.title}"},
        )
        messages.success(self.request, "Task created successfully.")
        return response


class TaskUpdateView(TaskQuerysetMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_task_details(request.user, self.object):
            messages.error(request, "You do not have permission to edit this task.")
            return redirect(self.object.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        current = self.get_queryset().get(pk=self.object.pk)
        old_attachment = current.attachment
        response = super().form_valid(form)
        if old_attachment and (not self.object.attachment or old_attachment.name != self.object.attachment.name):
            delete_uploaded_file(old_attachment)
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

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not can_edit_task_details(request.user, self.object):
            messages.error(request, "You do not have permission to delete this task.")
            return redirect(self.object.get_absolute_url())
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        task_name = self.object.title
        task_id = self.object.pk
        if self.object.attachment:
            delete_uploaded_file(self.object.attachment)
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
        if not can_update_task_status(request.user, task):
            messages.error(request, "You do not have permission to update this task status.")
            return redirect(task.get_absolute_url())
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


class TaskStatusUpdateView(TaskQuerysetMixin, View):
    allowed_statuses = {status for status, _label in Task.STATUS_CHOICES}

    def post(self, request, *args, **kwargs):
        task = get_object_or_404(self.get_queryset(), pk=kwargs["pk"])
        if not can_update_task_status(request.user, task):
            return JsonResponse({"ok": False, "error": "Permission denied."}, status=403)
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)

        status = payload.get("status")
        if status not in self.allowed_statuses:
            return JsonResponse({"ok": False, "error": "Invalid task status."}, status=400)

        if task.status == status:
            return JsonResponse({"ok": True, "status": task.status, "message": "Task already has this status."})

        old_status = task.status
        task.status = status
        task.completed_at = timezone.now() if status == "done" else None
        task.save(update_fields=["status", "completed_at", "updated_at"])
        ActivityLog.objects.create(
            actor=request.user,
            action="status_changed",
            object_type="task",
            object_id=task.pk,
            metadata={
                "object_name": task.title,
                "message": f"Moved task {task.title} from {old_status} to {status}",
            },
        )
        return JsonResponse(
            {
                "ok": True,
                "status": task.status,
                "status_label": task.get_status_display(),
                "message": f"{task.title} moved to {task.get_status_display()}.",
            }
        )
