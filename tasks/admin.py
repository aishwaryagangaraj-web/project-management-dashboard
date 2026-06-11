from django.contrib import admin

from .models import Task, TaskComment


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "assignee", "status", "priority", "due_date")
    list_filter = ("status", "priority", "project")
    search_fields = ("title", "description", "project__name", "assignee__username")


@admin.register(TaskComment)
class TaskCommentAdmin(admin.ModelAdmin):
    list_display = ("task", "user", "created_at")
    search_fields = ("task__title", "user__username", "comment")
