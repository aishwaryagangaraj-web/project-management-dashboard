from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.access import (
    can_create_project,
    can_create_task,
    can_edit_task_details,
    can_manage_project,
    can_manage_task_content,
    can_update_task_status,
    visible_projects_queryset,
    visible_tasks_queryset,
)
from analytics.models import ActivityLog
from notifications.models import Notification
from projects.models import Project
from reports.pdf import analytics_report_pdf
from tasks.models import Task, TaskComment
from tasks.models import validate_task_attachment

from .serializers import (
    NotificationSerializer,
    ProfileSerializer,
    ProjectSerializer,
    RegisterSerializer,
    TaskCommentSerializer,
    TaskSerializer,
)

User = get_user_model()


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile = getattr(user, "profile", None)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": getattr(profile, "role", "member"),
                },
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
            status=status.HTTP_201_CREATED,
        )


class ProfileAPIView(APIView):
    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data)

    def patch(self, request):
        serializer = ProfileSerializer(request.user.profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def put(self, request):
        return self.patch(request)


class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer

    def get_queryset(self):
        return visible_projects_queryset(self.request.user, Project.objects.select_related("owner").prefetch_related("members"))

    def perform_create(self, serializer):
        if not can_create_project(self.request.user):
            raise PermissionDenied("You do not have permission to create projects.")
        project = serializer.save(owner=self.request.user)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="created",
            object_type="project",
            object_id=project.pk,
            metadata={"object_name": project.name, "message": f"Created project {project.name}"},
        )

    def perform_update(self, serializer):
        project = self.get_object()
        if not can_manage_project(self.request.user, project):
            raise PermissionDenied("You do not have permission to update this project.")
        project = serializer.save()
        ActivityLog.objects.create(
            actor=self.request.user,
            action="updated",
            object_type="project",
            object_id=project.pk,
            metadata={"object_name": project.name, "message": f"Updated project {project.name}"},
        )

    def perform_destroy(self, instance):
        if not can_manage_project(self.request.user, instance):
            raise PermissionDenied("You do not have permission to delete this project.")
        project_name = instance.name
        project_id = instance.pk
        instance.delete()
        ActivityLog.objects.create(
            actor=self.request.user,
            action="deleted",
            object_type="project",
            object_id=project_id,
            metadata={"object_name": project_name, "message": f"Deleted project {project_name}"},
        )


class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        return visible_tasks_queryset(
            self.request.user,
            Task.objects.select_related("project", "assignee", "reporter", "project__owner").annotate(
                comment_count=Count("comments", distinct=True)
            ),
        )

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        if not can_create_task(self.request.user, project):
            raise PermissionDenied("You do not have permission to create tasks for this project.")
        task = serializer.save(reporter=self.request.user)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="created",
            object_type="task",
            object_id=task.pk,
            metadata={"object_name": task.title, "message": f"Created task {task.title}"},
        )

    def perform_update(self, serializer):
        task = self.get_object()
        if not can_edit_task_details(self.request.user, task):
            raise PermissionDenied("You do not have permission to update this task.")
        old_attachment = task.attachment
        task = serializer.save()
        if old_attachment and old_attachment.name != getattr(task.attachment, "name", None):
            old_attachment.delete(save=False)
        ActivityLog.objects.create(
            actor=self.request.user,
            action="updated",
            object_type="task",
            object_id=task.pk,
            metadata={"object_name": task.title, "message": f"Updated task {task.title}"},
        )

    def perform_destroy(self, instance):
        if not can_edit_task_details(self.request.user, instance):
            raise PermissionDenied("You do not have permission to delete this task.")
        task_name = instance.title
        task_id = instance.pk
        if instance.attachment:
            instance.attachment.delete(save=False)
        instance.delete()
        ActivityLog.objects.create(
            actor=self.request.user,
            action="deleted",
            object_type="task",
            object_id=task_id,
            metadata={"object_name": task_name, "message": f"Deleted task {task_name}"},
        )

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        task = self.get_object()
        if request.method == "GET":
            serializer = TaskCommentSerializer(task.comments.select_related("user", "user__profile").all(), many=True)
            return Response(serializer.data)
        if not can_manage_task_content(request.user, task):
            raise PermissionDenied("You do not have permission to comment on this task.")
        serializer = TaskCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = serializer.save(task=task, user=request.user)
        ActivityLog.objects.create(
            actor=request.user,
            action="commented",
            object_type="task",
            object_id=task.pk,
            metadata={"object_name": task.title, "message": f"Commented on task {task.title}"},
        )
        return Response(TaskCommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["put", "patch", "delete"], url_path=r"comments/(?P<comment_pk>[^/.]+)")
    def comment_detail(self, request, pk=None, comment_pk=None):
        task = self.get_object()
        comment = get_object_or_404(TaskComment, pk=comment_pk, task=task)
        if request.method in {"PUT", "PATCH"}:
            if request.user != comment.user and not can_manage_task_content(request.user, task):
                raise PermissionDenied("You do not have permission to edit this comment.")
            serializer = TaskCommentSerializer(comment, data=request.data, partial=request.method == "PATCH")
            serializer.is_valid(raise_exception=True)
            comment = serializer.save()
            return Response(TaskCommentSerializer(comment).data)
        if request.user != comment.user and not can_manage_task_content(request.user, task):
            raise PermissionDenied("You do not have permission to delete this comment.")
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post", "delete"], url_path="upload")
    def upload(self, request, pk=None):
        task = self.get_object()
        if not can_manage_task_content(request.user, task):
            raise PermissionDenied("You do not have permission to modify attachments for this task.")
        if request.method == "DELETE":
            if task.attachment:
                task.attachment.delete(save=False)
                task.attachment = None
                task.save(update_fields=["attachment", "updated_at"])
            return Response(status=status.HTTP_204_NO_CONTENT)

        upload = request.FILES.get("attachment")
        if not upload:
            return Response({"detail": "Choose a file to upload."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_task_attachment(upload)
        except ValidationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        if task.attachment:
            task.attachment.delete(save=False)
        task.attachment.save(upload.name, upload, save=True)
        return Response(self.get_serializer(task).data, status=status.HTTP_200_OK)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=["post"], url_path="read")
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response(self.get_serializer(notification).data)


class AnalyticsStatsAPIView(APIView):
    def get(self, request):
        projects = visible_projects_queryset(request.user, Project.objects.all())
        tasks = visible_tasks_queryset(request.user, Task.objects.all())
        project_status_labels = dict(Project.STATUS_CHOICES)
        task_status_labels = dict(Task.STATUS_CHOICES)
        projects_by_status = list(projects.values("status").annotate(total=Count("id")).order_by("status"))
        tasks_by_status = list(tasks.values("status").annotate(total=Count("id")).order_by("status"))
        monthly_completion = list(
            tasks.filter(status="done", completed_at__isnull=False)
            .annotate(month=TruncMonth("completed_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )
        return Response(
            {
                "projects": {
                    "total": projects.count(),
                    "by_status": projects_by_status,
                    "labels": [project_status_labels.get(item["status"], item["status"]) for item in projects_by_status],
                },
                "tasks": {
                    "total": tasks.count(),
                    "completed": tasks.filter(status="done").count(),
                    "overdue": tasks.filter(status__in=["todo", "in_progress"], due_date__lt=Task.today()).count(),
                    "by_status": tasks_by_status,
                    "labels": [task_status_labels.get(item["status"], item["status"]) for item in tasks_by_status],
                },
                "monthly_completion": [
                    {"month": item["month"].strftime("%b %Y"), "total": item["total"]} for item in monthly_completion
                ],
            }
        )
