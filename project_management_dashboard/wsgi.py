"""WSGI config for project_management_dashboard project."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project_management_dashboard.settings")

application = get_wsgi_application()
