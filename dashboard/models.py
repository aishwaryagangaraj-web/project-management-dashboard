from django.db import models


class DashboardPreference(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE, related_name="dashboard_preference")
    compact_mode = models.BooleanField(default=False)
    default_date_range = models.CharField(max_length=30, default="30d")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} dashboard preferences"

