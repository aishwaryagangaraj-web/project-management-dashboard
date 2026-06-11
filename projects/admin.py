from django.contrib import admin

from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "status", "priority", "due_date", "updated_at")
    list_filter = ("status", "priority", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "description", "owner__username")
    filter_horizontal = ("members",)
