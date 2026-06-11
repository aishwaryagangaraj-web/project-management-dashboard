from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("actor", "action", "object_type", "object_id", "created_at")
    list_filter = ("action", "object_type", "created_at")
    search_fields = ("actor__username", "object_type")
