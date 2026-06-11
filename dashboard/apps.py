from django.apps import AppConfig
from django.db.models.signals import post_migrate


class DashboardConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dashboard"

    def ready(self):
        post_migrate.connect(create_demo_data_after_migrate, sender=self, dispatch_uid="dashboard.create_demo_data_after_migrate")


def create_demo_data_after_migrate(sender, **kwargs):
    from dashboard.demo_data import ensure_demo_data

    ensure_demo_data()
