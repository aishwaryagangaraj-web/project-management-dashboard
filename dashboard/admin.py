from django.contrib import admin

from .models import DashboardPreference


@admin.register(DashboardPreference)
class DashboardPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "compact_mode", "default_date_range", "updated_at")
