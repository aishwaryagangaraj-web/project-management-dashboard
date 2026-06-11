"""ASGI config for project_management_dashboard project."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_management_dashboard.settings")

application = get_asgi_application()
