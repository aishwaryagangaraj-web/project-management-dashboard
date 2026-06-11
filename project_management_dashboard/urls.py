from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("projects/", include("projects.urls")),
    path("tasks/", include("tasks.urls")),
    path("notifications/", include("notifications.urls")),
    path("analytics/", include("analytics.urls")),
    path("reports/", include("reports.urls")),
    path("api/", include("api.urls")),
    path("", include("dashboard.urls")),
]

handler404 = "dashboard.views.handler404"
handler500 = "dashboard.views.handler500"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
