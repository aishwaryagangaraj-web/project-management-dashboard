from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views import View

from accounts.access import can_manage_project, visible_projects_queryset, visible_tasks_queryset
from analytics.models import ActivityLog
from projects.models import Project
from tasks.models import Task

from .pdf import analytics_report_pdf, project_report_pdf, task_report_pdf


class ProjectReportView(LoginRequiredMixin, View):
    def get(self, request, slug):
        project = get_object_or_404(visible_projects_queryset(request.user, Project.objects.select_related("owner")), slug=slug)
        tasks = visible_tasks_queryset(
            request.user,
            project.tasks.select_related("assignee", "reporter", "project", "project__owner"),
        )
        activities = ActivityLog.objects.filter(object_type="project", object_id=project.pk).order_by("-created_at")[:12]
        pdf = project_report_pdf(project, tasks, activities)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="project-{project.slug}.pdf"'
        return response


class TaskReportView(LoginRequiredMixin, View):
    def get(self, request, pk):
        task = get_object_or_404(visible_tasks_queryset(request.user, Task.objects.select_related("project", "assignee", "reporter", "project__owner")), pk=pk)
        comments = task.comments.select_related("user", "user__profile").order_by("created_at")
        activities = ActivityLog.objects.filter(object_type="task", object_id=task.pk).order_by("-created_at")[:12]
        pdf = task_report_pdf(task, comments, activities)
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="task-{task.pk}.pdf"'
        return response


class AnalyticsReportView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        projects = visible_projects_queryset(
            user,
            Project.objects.select_related("owner").prefetch_related("tasks"),
        ).annotate(
            total_tasks=Count("tasks", distinct=True),
            completed_tasks=Count("tasks", filter=Q(tasks__status="done"), distinct=True),
        )
        tasks = visible_tasks_queryset(
            user,
            Task.objects.select_related("project", "assignee", "reporter", "project__owner"),
        )
        projects_by_status = list(projects.values("status").annotate(total=Count("id", distinct=True)).order_by("status"))
        tasks_by_status = list(tasks.values("status").annotate(total=Count("id")).order_by("status"))
        monthly_completion = list(
            tasks.filter(status="done", completed_at__isnull=False)
            .annotate(month=TruncMonth("completed_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )
        today = Task.today()
        project_rows = [
            {
                "name": project.name,
                "progress": project.progress,
                "status": project.status,
                "status_display": project.get_status_display(),
                "total_tasks": getattr(project, "total_tasks", 0),
                "completed_tasks": getattr(project, "completed_tasks", 0),
                "due_date": project.due_date,
            }
            for project in projects.order_by("-updated_at")
        ]
        task_insights = {
            "high_priority": [
                {
                    "title": task.title,
                    "project": task.project.name,
                    "status": task.status,
                    "status_display": task.get_status_display(),
                    "priority": task.priority,
                    "priority_display": task.get_priority_display(),
                    "due_date": task.due_date,
                }
                for task in tasks.filter(priority__in=["high", "urgent"]).order_by("due_date", "-updated_at")[:8]
            ],
            "overdue": [
                {
                    "title": task.title,
                    "project": task.project.name,
                    "status": task.status,
                    "status_display": task.get_status_display(),
                    "priority": task.priority,
                    "priority_display": task.get_priority_display(),
                    "due_date": task.due_date,
                }
                for task in tasks.filter(status__in=["todo", "in_progress", "review", "blocked"], due_date__lt=today).order_by("due_date")[:8]
            ],
            "blocked": [
                {
                    "title": task.title,
                    "project": task.project.name,
                    "status": task.status,
                    "status_display": task.get_status_display(),
                    "priority": task.priority,
                    "priority_display": task.get_priority_display(),
                    "due_date": task.due_date,
                }
                for task in tasks.filter(status="blocked").order_by("due_date", "-updated_at")[:8]
            ],
            "recently_completed": [
                {
                    "title": task.title,
                    "project": task.project.name,
                    "status": task.status,
                    "status_display": task.get_status_display(),
                    "priority": task.priority,
                    "priority_display": task.get_priority_display(),
                    "completed_at": task.completed_at,
                }
                for task in tasks.filter(status="done").order_by("-completed_at")[:8]
            ],
        }
        summary = {
            "projects": projects.count(),
            "active_projects": projects.exclude(status__in=["completed", "archived"]).count(),
            "tasks": tasks.count(),
            "completed_tasks": tasks.filter(status="done").count(),
            "pending_tasks": tasks.filter(status__in=["todo", "in_progress", "review", "blocked"]).count(),
            "overdue_tasks": tasks.filter(status__in=["todo", "in_progress", "review", "blocked"], due_date__lt=Task.today()).count(),
        }
        pdf = analytics_report_pdf(
            summary,
            projects_by_status,
            tasks_by_status,
            monthly_completion,
            project_rows=project_rows,
            task_insights=task_insights,
        )
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="analytics-summary.pdf"'
        return response
