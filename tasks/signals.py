from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from notifications.services import send_task_assignment_notification

from .models import Task


@receiver(pre_save, sender=Task)
def cache_previous_task_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._previous_assignee_id = None
        return
    previous = sender.objects.filter(pk=instance.pk).values("assignee_id").first()
    instance._previous_assignee_id = previous["assignee_id"] if previous else None


@receiver(post_save, sender=Task)
def notify_task_assignment(sender, instance, created, **kwargs):
    previous_assignee_id = getattr(instance, "_previous_assignee_id", None)
    if created and instance.assignee_id:
        send_task_assignment_notification(instance)
    elif previous_assignee_id != instance.assignee_id and instance.assignee_id:
        send_task_assignment_notification(instance)
