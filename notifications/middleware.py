import logging

from notifications.services import send_daily_task_reminders

logger = logging.getLogger(__name__)


class TaskReminderMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return response
        if request.method not in {"GET", "HEAD"}:
            return response
        if request.path.startswith("/api/") or request.path.startswith("/admin/"):
            return response

        try:
            send_daily_task_reminders(request.user)
        except Exception:  # pragma: no cover - defensive logging only
            logger.exception("Failed to send task reminders for %s", request.user.pk)
        return response
