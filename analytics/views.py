from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.views.generic import TemplateView

from accounts.access import visible_tasks_queryset
from projects.models import Project
from tasks.models import Task


class AnalyticsOverviewView(LoginRequiredMixin, TemplateView):
    template_name = "analytics/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        projects = Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()
        tasks = visible_tasks_queryset(user, Task.objects.all())
        project_status_labels = dict(Project.STATUS_CHOICES)
        task_status_labels = dict(Task.STATUS_CHOICES)
        task_priority_labels = dict(Task.PRIORITY_CHOICES)
        projects_by_status = list(projects.values("status").annotate(total=Count("id")).order_by("status"))
        tasks_by_status = list(tasks.values("status").annotate(total=Count("id")).order_by("status"))
        tasks_by_priority = list(tasks.values("priority").annotate(total=Count("id")).order_by("priority"))
        monthly_completion = list(
            tasks.filter(status="done", completed_at__isnull=False)
            .annotate(month=TruncMonth("completed_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        context.update(
            {
                "projects_by_status": projects_by_status,
                "tasks_by_status": tasks_by_status,
                "tasks_by_priority": tasks_by_priority,
                "task_status_chart": {
                    "labels": [task_status_labels.get(item["status"], item["status"]) for item in tasks_by_status],
                    "data": [item["total"] for item in tasks_by_status],
                },
                "project_status_chart": {
                    "labels": [project_status_labels.get(item["status"], item["status"]) for item in projects_by_status],
                    "data": [item["total"] for item in projects_by_status],
                },
                "task_priority_chart": {
                    "labels": [task_priority_labels.get(item["priority"], item["priority"]) for item in tasks_by_priority],
                    "data": [item["total"] for item in tasks_by_priority],
                },
                "monthly_completion_chart": {
                    "labels": [item["month"].strftime("%b %Y") for item in monthly_completion],
                    "data": [item["total"] for item in monthly_completion],
                },
            }
        )
        return context
