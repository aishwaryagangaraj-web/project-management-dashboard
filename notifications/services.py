from __future__ import annotations

from datetime import timedelta
from urllib.parse import urljoin

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from accounts.access import visible_tasks_queryset


def build_absolute_url(path: str) -> str:
    base = getattr(settings, "SITE_URL", "").rstrip("/")
    if not base:
        return path
    return urljoin(f"{base}/", path.lstrip("/"))


def _send_text_email(subject: str, body: str, recipient_email: str):
    if not recipient_email:
        return
    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, "DEFAULT_FROM_EMAIL", None),
        recipient_list=[recipient_email],
        fail_silently=False,
    )


def send_task_assignment_notification(task, recipient=None):
    from notifications.models import Notification

    recipient = recipient or task.assignee
    if not recipient or not recipient.email:
        return

    title = "New task assigned"
    message = f"You were assigned to {task.title} in {task.project.name}."
    Notification.objects.get_or_create(
        recipient=recipient,
        title=title,
        message=message,
        link=task.get_absolute_url(),
        defaults={"level": "info"},
    )
    _send_text_email(
        subject=f"ProjectFlow assignment: {task.title}",
        body="\n".join(
            [
                f"Project: {task.project.name}",
                f"Task: {task.title}",
                f"Due date: {task.due_date or 'Not set'}",
                f"Link: {build_absolute_url(task.get_absolute_url())}",
            ]
        ),
        recipient_email=recipient.email,
    )


def send_daily_task_reminders(user):
    profile = getattr(user, "profile", None)
    if not profile or not getattr(user, "email", ""):
        return False

    today = timezone.localdate()
    if getattr(profile, "reminder_last_sent", None) and profile.reminder_last_sent.date() == today:
        return False

    from tasks.models import Task

    tasks = visible_tasks_queryset(
        user,
        Task.objects.select_related("project", "assignee", "reporter"),
    )
    overdue = list(tasks.filter(status__in=["todo", "in_progress", "review", "blocked"], due_date__lt=today))
    due_tomorrow = list(tasks.filter(status__in=["todo", "in_progress", "review", "blocked"], due_date=today + timedelta(days=1)))

    if not overdue and not due_tomorrow:
        return False

    subject = "ProjectFlow task reminder"
    lines = [f"Hello {user.get_username()},", ""]

    if overdue:
        lines.append("Overdue tasks:")
        for task in overdue:
            lines.extend(
                [
                    f"- {task.project.name} / {task.title} | Due: {task.due_date}",
                    f"  {build_absolute_url(task.get_absolute_url())}",
                ]
            )
        lines.append("")

    if due_tomorrow:
        lines.append("Due tomorrow:")
        for task in due_tomorrow:
            lines.extend(
                [
                    f"- {task.project.name} / {task.title} | Due: {task.due_date}",
                    f"  {build_absolute_url(task.get_absolute_url())}",
                ]
            )

    body = "\n".join(lines)
    _send_text_email(subject=subject, body=body, recipient_email=user.email)

    profile.reminder_last_sent = timezone.now()
    profile.save(update_fields=["reminder_last_sent", "updated_at"])
    return True
