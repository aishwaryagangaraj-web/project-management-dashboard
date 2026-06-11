from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import render
from django.conf import settings
from django.views.generic import TemplateView

from accounts.access import can_create_project, can_create_task, is_admin, user_role, visible_tasks_queryset
from analytics.models import ActivityLog
from notifications.models import Notification
from projects.models import Project
from tasks.models import Task


class HomeDashboardView(TemplateView):
    template_name = "dashboard/home.html"
    landing_template_name = "dashboard/landing.html"

    def get_template_names(self):
        if self.request.user.is_authenticated:
            return [self.template_name]
        return [self.landing_template_name]

    def get_context_data(self, **kwargs):
        if not self.request.user.is_authenticated:
            return {
                "public_project_count": Project.objects.count(),
                "public_task_count": Task.objects.count(),
                "public_member_count": get_user_model().objects.count(),
                "public_role": "Administrator" if is_admin(self.request.user) else "Guest",
                "demo_video_url": settings.DEMO_VIDEO_URL,
                "demo_video_thumbnail": "images/dashboard-preview.png",
            }

        context = super().get_context_data(**kwargs)
        user = self.request.user
        projects = Project.objects.filter(Q(owner=user) | Q(members=user)).distinct()
        tasks = visible_tasks_queryset(user, Task.objects.all())
        project_status_labels = dict(Project.STATUS_CHOICES)
        task_status_labels = dict(Task.STATUS_CHOICES)
        projects_by_status = list(projects.values("status").annotate(total=Count("id")).order_by("status"))
        tasks_by_status = list(tasks.values("status").annotate(total=Count("id")).order_by("status"))
        project_progress = list(projects.order_by("-updated_at")[:8])
        monthly_completion = list(
            tasks.filter(status="done", completed_at__isnull=False)
            .annotate(month=TruncMonth("completed_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )

        context.update(
            {
                "user_role": user_role(user),
                "can_create_project": can_create_project(user),
                "can_create_task": can_create_task(user),
                "project_count": projects.count(),
                "active_project_count": projects.filter(status="active").count(),
                "task_count": tasks.count(),
                "completed_task_count": tasks.filter(status="done").count(),
                "pending_task_count": tasks.exclude(status="done").count(),
                "overdue_task_count": tasks.filter(status__in=["todo", "in_progress"], due_date__lt=Task.today()).count(),
                "recent_projects": projects.order_by("-updated_at")[:5],
                "recent_tasks": tasks.order_by("-updated_at")[:7],
                "task_status_summary": tasks.values("status").annotate(total=Count("id")).order_by("status"),
                "unread_notifications": Notification.objects.filter(recipient=user, is_read=False)[:6],
                "recent_activity": ActivityLog.objects.filter(actor=user)[:8],
                "task_status_chart": {
                    "labels": [task_status_labels.get(item["status"], item["status"]) for item in tasks_by_status],
                    "data": [item["total"] for item in tasks_by_status],
                },
                "project_status_chart": {
                    "labels": [project_status_labels.get(item["status"], item["status"]) for item in projects_by_status],
                    "data": [item["total"] for item in projects_by_status],
                },
                "project_progress_chart": {
                    "labels": [project.name for project in project_progress],
                    "data": [project.progress for project in project_progress],
                },
                "monthly_completion_chart": {
                    "labels": [item["month"].strftime("%b %Y") for item in monthly_completion],
                    "data": [item["total"] for item in monthly_completion],
                },
            }
        )
        return context


class ArchitectureView(TemplateView):
    template_name = "dashboard/architecture.html"


def handler404(request, exception):
    return render(request, "404.html", status=404)


def handler500(request):
    return render(request, "500.html", status=500)
