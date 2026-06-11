from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from math import ceil

from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.utils import timezone
from django.views.generic import TemplateView

from accounts.access import visible_tasks_queryset
from analytics.models import ActivityLog
from projects.models import Project
from tasks.models import Task


def _local_date(value):
    if not value:
        return None
    return timezone.localdate(value)


def _percent(value: float | int) -> int:
    return max(0, min(100, round(value)))


def _safe_rate(numerator: float, denominator: float) -> int:
    if not denominator:
        return 0
    return _percent((numerator / denominator) * 100)


def _trend(current: float, previous: float) -> int:
    if previous == 0:
        return 100 if current > 0 else 0
    return _percent(((current - previous) / previous) * 100)


def _average_completion_hours(task_list) -> float:
    completed = [task for task in task_list if task.completed_at and task.created_at]
    if not completed:
        return 0

    total_hours = 0.0
    for task in completed:
        total_hours += max(0.5, (task.completed_at - task.created_at).total_seconds() / 3600)
    return round(total_hours / len(completed), 1)


class AnalyticsOverviewView(LoginRequiredMixin, TemplateView):
    template_name = "analytics/overview.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        prev_week_start = week_start - timedelta(days=7)

        projects_qs = (
            Project.objects.filter(Q(owner=user) | Q(members=user))
            .distinct()
            .select_related("owner")
            .prefetch_related("members")
        )
        tasks_qs = visible_tasks_queryset(
            user,
            Task.objects.select_related("project", "assignee", "reporter", "project__owner"),
        )

        projects = list(projects_qs)
        tasks = list(tasks_qs)
        User = get_user_model()

        project_status_labels = dict(Project.STATUS_CHOICES)
        task_status_labels = dict(Task.STATUS_CHOICES)
        task_priority_labels = dict(Task.PRIORITY_CHOICES)

        projects_by_status = list(
            projects_qs.values("status")
            .annotate(total=Count("id", distinct=True))
            .order_by("status")
        )
        tasks_by_status = list(tasks_qs.values("status").annotate(total=Count("id")).order_by("status"))
        tasks_by_priority = list(tasks_qs.values("priority").annotate(total=Count("id")).order_by("priority"))

        task_ids = [task.pk for task in tasks]
        project_ids = [project.pk for project in projects]

        completed_tasks = [task for task in tasks if task.status == "done"]
        pending_tasks = [task for task in tasks if task.status != "done"]
        blocked_tasks = [task for task in tasks if task.status == "blocked"]
        overdue_tasks = [
            task
            for task in tasks
            if task.status != "done" and task.due_date and task.due_date < today
        ]
        assigned_tasks = [task for task in tasks if task.assignee_id]
        active_projects = [project for project in projects if project.status not in {"completed", "archived"}]

        on_time_completed = [
            task
            for task in completed_tasks
            if task.due_date and task.completed_at and _local_date(task.completed_at) <= task.due_date
        ]

        project_task_map: dict[int, dict[str, int]] = defaultdict(
            lambda: {"total": 0, "completed": 0, "blocked": 0, "overdue": 0}
        )
        for task in tasks:
            bucket = project_task_map[task.project_id]
            bucket["total"] += 1
            if task.status == "done":
                bucket["completed"] += 1
            if task.status == "blocked":
                bucket["blocked"] += 1
            if task.status != "done" and task.due_date and task.due_date < today:
                bucket["overdue"] += 1

        project_rows = []
        for project in sorted(projects, key=lambda item: item.updated_at, reverse=True):
            bucket = project_task_map[project.pk]
            total_tasks = bucket["total"]
            completed_count = bucket["completed"]
            progress = round((completed_count / total_tasks) * 100) if total_tasks else 0
            project_rows.append(
                {
                    "project": project,
                    "total_tasks": total_tasks,
                    "completed_tasks": completed_count,
                    "blocked_tasks": bucket["blocked"],
                    "overdue_tasks": bucket["overdue"],
                    "progress": progress,
                    "status_label": project.get_status_display(),
                    "priority_label": project.get_priority_display(),
                }
            )

        weekly_stats = []
        week_labels = []
        weekly_created = []
        weekly_completed = []
        weekly_open = []
        weekly_overdue = []
        weekly_sprint_rate = []
        weekly_productivity = []
        weekly_efficiency = []
        weekly_avg_completion = []
        burndown_remaining = []
        burndown_ideal = []

        cumulative_completed = 0
        total_task_count = len(tasks)
        eight_weeks_ago = week_start - timedelta(weeks=7)

        for index in range(8):
            start = eight_weeks_ago + timedelta(weeks=index)
            end = start + timedelta(days=6)
            week_tasks_created = [
                task
                for task in tasks
                if task.created_at and start <= _local_date(task.created_at) <= end
            ]
            week_tasks_completed = [
                task
                for task in tasks
                if task.completed_at and start <= _local_date(task.completed_at) <= end
            ]
            week_tasks_open = [
                task
                for task in tasks
                if task.created_at
                and _local_date(task.created_at) <= end
                and not (task.completed_at and _local_date(task.completed_at) <= end)
            ]
            week_tasks_overdue = [
                task
                for task in tasks
                if task.due_date and task.status != "done" and task.due_date < end
            ]
            week_tasks_on_time = [
                task
                for task in week_tasks_completed
                if task.due_date and task.completed_at and _local_date(task.completed_at) <= task.due_date
            ]

            created_count = len(week_tasks_created)
            completed_count = len(week_tasks_completed)
            open_count = len(week_tasks_open)
            overdue_count = len(week_tasks_overdue)
            sprint_rate = _safe_rate(completed_count, created_count or open_count or 1)
            efficiency = _safe_rate(len(week_tasks_on_time), max(len(week_tasks_completed), 1))
            productivity = max(
                0,
                min(
                    100,
                    round(
                        (sprint_rate * 0.55)
                        + (efficiency * 0.25)
                        - (_safe_rate(overdue_count, max(total_task_count, 1)) * 0.2)
                    ),
                ),
            )
            avg_completion = _average_completion_hours(week_tasks_completed)

            cumulative_completed += completed_count
            weekly_stats.append(
                {
                    "start": start,
                    "end": end,
                    "created": created_count,
                    "completed": completed_count,
                    "open": open_count,
                    "overdue": overdue_count,
                    "sprint": sprint_rate,
                    "productivity": productivity,
                    "efficiency": efficiency,
                    "avg_completion": avg_completion,
                }
            )
            week_labels.append(start.strftime("%b %d"))
            weekly_created.append(created_count)
            weekly_completed.append(completed_count)
            weekly_open.append(open_count)
            weekly_overdue.append(overdue_count)
            weekly_sprint_rate.append(sprint_rate)
            weekly_productivity.append(productivity)
            weekly_efficiency.append(efficiency)
            weekly_avg_completion.append(avg_completion)
            burndown_remaining.append(max(0, total_task_count - cumulative_completed))
            burndown_ideal.append(max(0, round(total_task_count * (1 - ((index + 1) / 8)))))

        current_stats = weekly_stats[-1]
        previous_stats = weekly_stats[-2] if len(weekly_stats) > 1 else weekly_stats[-1]

        all_avg_completion = _average_completion_hours(completed_tasks)
        previous_week_completed = previous_stats["completed"] if previous_stats else 0
        previous_week_created = previous_stats["created"] if previous_stats else 0
        previous_week_sprint = previous_stats["sprint"] if previous_stats else 0
        previous_week_productivity = previous_stats["productivity"] if previous_stats else 0
        previous_week_efficiency = previous_stats["efficiency"] if previous_stats else 0
        previous_week_overdue = previous_stats["overdue"] if previous_stats else 0
        previous_week_avg_completion = previous_stats["avg_completion"] if previous_stats else 0

        current_week_completed = current_stats["completed"]
        current_week_created = current_stats["created"]
        current_week_sprint = current_stats["sprint"]
        current_week_productivity = current_stats["productivity"]
        current_week_efficiency = current_stats["efficiency"]
        current_week_overdue = current_stats["overdue"]
        current_week_avg_completion = current_stats["avg_completion"]

        productivity_score = _percent(
            (
                (_safe_rate(len(completed_tasks), max(total_task_count, 1)) * 0.55)
                + (_safe_rate(len(on_time_completed), max(len(completed_tasks), 1)) * 0.3)
                + (current_week_efficiency * 0.15)
                - (_safe_rate(len(overdue_tasks), max(len(pending_tasks), 1)) * 0.4)
                - (_safe_rate(len(blocked_tasks), max(len(tasks), 1)) * 0.2)
            )
        )
        sprint_completion_rate = current_week_sprint
        overdue_risk = _safe_rate(len(overdue_tasks), max(len(pending_tasks), 1))
        team_efficiency = _safe_rate(len(on_time_completed), max(len(assigned_tasks), 1))
        weekly_velocity = current_week_completed

        metrics = {
            "productivity_score": productivity_score,
            "productivity_score_trend": _trend(current_week_productivity, previous_week_productivity),
            "sprint_completion_rate": sprint_completion_rate,
            "sprint_completion_rate_trend": _trend(current_week_sprint, previous_week_sprint),
            "avg_completion_time": all_avg_completion,
            "avg_completion_time_trend": _trend(previous_week_avg_completion, current_week_avg_completion),
            "overdue_risk": overdue_risk,
            "overdue_risk_trend": _trend(current_week_overdue, previous_week_overdue),
            "team_efficiency": team_efficiency,
            "team_efficiency_trend": _trend(current_week_efficiency, previous_week_efficiency),
            "weekly_velocity": weekly_velocity,
            "weekly_velocity_trend": _trend(current_week_completed, previous_week_completed),
            "open_tasks": len(pending_tasks),
            "completed_tasks": len(completed_tasks),
            "total_tasks": total_task_count,
            "active_projects": len(active_projects),
            "project_count": len(projects),
        }

        member_map = defaultdict(lambda: {"total": 0, "done": 0, "blocked": 0, "overdue": 0, "open": 0})
        for task in tasks:
            if not task.assignee:
                continue
            bucket = member_map[task.assignee]
            bucket["total"] += 1
            if task.status == "done":
                bucket["done"] += 1
            elif task.status == "blocked":
                bucket["blocked"] += 1
            else:
                bucket["open"] += 1
            if task.due_date and task.status != "done" and task.due_date < today:
                bucket["overdue"] += 1

        members = list(
            User.objects.filter(
                Q(owned_projects__id__in=project_ids)
                | Q(projects__id__in=project_ids)
                | Q(assigned_tasks__id__in=task_ids)
            )
            .distinct()
            .select_related("profile")
        )

        team_rows = []
        for member in members:
            bucket = member_map.get(member, {"total": 0, "done": 0, "blocked": 0, "overdue": 0, "open": 0})
            efficiency = _safe_rate(bucket["done"], max(bucket["total"], 1))
            team_rows.append(
                {
                    "member": member,
                    "name": member.get_username(),
                    "completed": bucket["done"],
                    "assigned": bucket["total"],
                    "blocked": bucket["blocked"],
                    "overdue": bucket["overdue"],
                    "open": bucket["open"],
                    "efficiency": efficiency,
                    "workload": bucket["total"],
                }
            )
        team_rows.sort(key=lambda row: (row["completed"], -row["overdue"], row["assigned"]), reverse=True)
        workload_rows = team_rows[:8]

        activity_logs = list(
            ActivityLog.objects.filter(
                Q(object_type="task", object_id__in=task_ids)
                | Q(object_type="project", object_id__in=project_ids)
            )
            .select_related("actor")
            .order_by("-created_at")[:14]
        )

        ai_insights = []
        if overdue_tasks:
            ai_insights.append(
                {
                    "tone": "danger",
                    "title": "Overdue risk detected",
                    "text": f"{len(overdue_tasks)} visible tasks are overdue. Focus on blockers and overdue work first.",
                }
            )
        else:
            ai_insights.append(
                {
                    "tone": "success",
                    "title": "Delivery is stable",
                    "text": "No overdue tasks are visible right now. The delivery queue is currently healthy.",
                }
            )

        if blocked_tasks:
            ai_insights.append(
                {
                    "tone": "warning",
                    "title": "Task bottleneck",
                    "text": f"{len(blocked_tasks)} blocked tasks are slowing throughput. Clear dependencies or reassign them.",
                }
            )

        if weekly_velocity >= 4:
            ai_insights.append(
                {
                    "tone": "info",
                    "title": "Productivity trend",
                    "text": f"Weekly velocity is {weekly_velocity} completed tasks. Delivery throughput is trending well.",
                }
            )
        else:
            ai_insights.append(
                {
                    "tone": "warning",
                    "title": "Velocity is soft",
                    "text": f"Weekly velocity is {weekly_velocity} tasks. WIP may be too wide for the current team size.",
                }
            )

        remaining_work = len(pending_tasks) + len(overdue_tasks)
        predicted_days = ceil(remaining_work / max(weekly_velocity, 1) * 7)
        ai_insights.append(
            {
                "tone": "neutral",
                "title": "Completion prediction",
                "text": f"At the current pace, the visible backlog should clear in about {predicted_days} days.",
            }
        )

        task_status_colors = ["#2563eb", "#7c3aed", "#f59e0b", "#16a34a", "#dc2626"]
        project_status_colors = ["#2563eb", "#16a34a", "#f59e0b", "#0f172a", "#64748b"]
        trend_blue = "#2563eb"
        trend_green = "#16a34a"
        trend_amber = "#f59e0b"
        trend_red = "#dc2626"
        trend_indigo = "#7c3aed"
        trend_teal = "#0891b2"

        charts = {
            "taskStatus": {
                "type": "doughnut",
                "labels": [task_status_labels.get(item["status"], item["status"]) for item in tasks_by_status],
                "datasets": [
                    {
                        "label": "Tasks",
                        "data": [item["total"] for item in tasks_by_status],
                        "backgroundColor": task_status_colors[: len(tasks_by_status)] or task_status_colors,
                        "borderColor": "transparent",
                        "borderWidth": 0,
                    }
                ],
                "options": {"cutout": "68%"},
            },
            "projectStatus": {
                "type": "doughnut",
                "labels": [project_status_labels.get(item["status"], item["status"]) for item in projects_by_status],
                "datasets": [
                    {
                        "label": "Projects",
                        "data": [item["total"] for item in projects_by_status],
                        "backgroundColor": project_status_colors[: len(projects_by_status)] or project_status_colors,
                        "borderColor": "transparent",
                        "borderWidth": 0,
                    }
                ],
                "options": {"cutout": "68%"},
            },
            "weeklyStack": {
                "type": "bar",
                "labels": week_labels,
                "datasets": [
                    {
                        "label": "Created",
                        "data": weekly_created,
                        "backgroundColor": "rgba(37, 99, 235, 0.75)",
                        "borderColor": "#2563eb",
                        "borderWidth": 0,
                        "stack": "weekly",
                    },
                    {
                        "label": "Completed",
                        "data": weekly_completed,
                        "backgroundColor": "rgba(22, 163, 74, 0.75)",
                        "borderColor": "#16a34a",
                        "borderWidth": 0,
                        "stack": "weekly",
                    },
                    {
                        "label": "Open",
                        "data": weekly_open,
                        "backgroundColor": "rgba(245, 158, 11, 0.6)",
                        "borderColor": "#f59e0b",
                        "borderWidth": 0,
                        "stack": "weekly",
                    },
                ],
                "options": {
                    "stacked": True,
                },
            },
            "productivityArea": {
                "type": "line",
                "labels": week_labels,
                "datasets": [
                    {
                        "label": "Productivity score",
                        "data": weekly_productivity,
                        "backgroundColor": "rgba(37, 99, 235, 0.16)",
                        "borderColor": trend_blue,
                        "fill": True,
                        "tension": 0.35,
                    }
                ],
            },
            "burndown": {
                "type": "line",
                "labels": week_labels,
                "datasets": [
                    {
                        "label": "Remaining work",
                        "data": burndown_remaining,
                        "backgroundColor": "rgba(220, 38, 38, 0.14)",
                        "borderColor": trend_red,
                        "fill": True,
                        "tension": 0.32,
                    },
                    {
                        "label": "Ideal burndown",
                        "data": burndown_ideal,
                        "backgroundColor": "transparent",
                        "borderColor": trend_indigo,
                        "borderDash": [6, 6],
                        "fill": False,
                        "tension": 0.2,
                    },
                ],
            },
            "timeline": {
                "type": "line",
                "labels": week_labels,
                "datasets": [
                    {
                        "label": "Created",
                        "data": weekly_created,
                        "backgroundColor": "rgba(37, 99, 235, 0.14)",
                        "borderColor": trend_blue,
                        "fill": False,
                        "tension": 0.35,
                    },
                    {
                        "label": "Completed",
                        "data": weekly_completed,
                        "backgroundColor": "rgba(22, 163, 74, 0.12)",
                        "borderColor": trend_green,
                        "fill": False,
                        "tension": 0.35,
                    },
                ],
            },
            "workload": {
                "type": "bar",
                "labels": [row["name"] for row in workload_rows],
                "datasets": [
                    {
                        "label": "Assigned tasks",
                        "data": [row["assigned"] for row in workload_rows],
                        "backgroundColor": "rgba(124, 58, 237, 0.75)",
                        "borderColor": trend_indigo,
                        "borderWidth": 0,
                    }
                ],
                "options": {
                    "indexAxis": "y",
                },
            },
        }

        kpi_cards = [
            {
                "id": "productivity-score",
                "label": "Productivity Score",
                "value": productivity_score,
                "suffix": "%",
                "trend": metrics["productivity_score_trend"],
                "tone": "accent-blue",
                "icon": "PS",
                "series": weekly_productivity,
                "help": "Balanced output score",
            },
            {
                "id": "sprint-completion-rate",
                "label": "Sprint Completion Rate",
                "value": sprint_completion_rate,
                "suffix": "%",
                "trend": metrics["sprint_completion_rate_trend"],
                "tone": "accent-green",
                "icon": "SC",
                "series": weekly_sprint_rate,
                "help": "This week delivery rate",
            },
            {
                "id": "avg-completion-time",
                "label": "Avg Task Completion Time",
                "value": all_avg_completion,
                "suffix": "h",
                "trend": metrics["avg_completion_time_trend"],
                "tone": "accent-amber",
                "icon": "AT",
                "series": weekly_avg_completion,
                "help": "Lower is faster",
                "decimals": 1,
            },
            {
                "id": "overdue-risk",
                "label": "Overdue Risk",
                "value": overdue_risk,
                "suffix": "%",
                "trend": metrics["overdue_risk_trend"],
                "tone": "accent-red",
                "icon": "OR",
                "series": weekly_overdue,
                "help": "Risk weighted backlog",
            },
            {
                "id": "team-efficiency",
                "label": "Team Efficiency",
                "value": team_efficiency,
                "suffix": "%",
                "trend": metrics["team_efficiency_trend"],
                "tone": "accent-indigo",
                "icon": "TE",
                "series": weekly_efficiency,
                "help": "On-time delivery rate",
            },
            {
                "id": "weekly-velocity",
                "label": "Weekly Velocity",
                "value": weekly_velocity,
                "suffix": "",
                "trend": metrics["weekly_velocity_trend"],
                "tone": "accent-teal",
                "icon": "WV",
                "series": weekly_completed,
                "help": "Completed tasks this week",
            },
        ]

        analytics_payload = {
            "kpis": kpi_cards,
            "charts": charts,
        }

        context.update(
            {
                "metrics": metrics,
                "analytics_payload": analytics_payload,
                "kpi_cards": kpi_cards,
                "project_rows": project_rows,
                "team_rows": workload_rows,
                "activity_feed": activity_logs,
                "ai_insights": ai_insights,
                "today": today,
                "task_status_summary": tasks_by_status,
                "project_status_summary": projects_by_status,
                "task_priority_summary": tasks_by_priority,
                "task_priority_labels": task_priority_labels,
                "current_week_completed": current_week_completed,
                "current_week_created": current_week_created,
                "avg_completion_hours": all_avg_completion,
                "overdue_tasks_count": len(overdue_tasks),
                "active_projects_count": len(active_projects),
            }
        )
        return context
