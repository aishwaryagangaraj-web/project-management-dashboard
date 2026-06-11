from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import Profile
from notifications.models import Notification
from projects.models import Project
from tasks.models import Task, TaskComment

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Profile
        fields = ["user", "role", "avatar", "department", "phone", "reminder_last_sent"]
        read_only_fields = ["role", "reminder_last_sent"]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        Profile.objects.get_or_create(user=user, defaults={"role": "member"})
        return user


class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    progress = serializers.IntegerField(read_only=True)
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "owner",
            "owner_username",
            "members",
            "status",
            "priority",
            "start_date",
            "due_date",
            "budget",
            "progress",
            "created_at",
            "updated_at",
        ]


class TaskSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())
    project_name = serializers.CharField(source="project.name", read_only=True)
    assignee = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), allow_null=True, required=False)
    assignee_username = serializers.CharField(source="assignee.username", read_only=True)
    reporter = serializers.CharField(source="reporter.username", read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    attachment_url = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id",
            "project",
            "project_name",
            "title",
            "description",
            "assignee",
            "assignee_username",
            "reporter",
            "status",
            "priority",
            "estimate_hours",
            "attachment",
            "attachment_url",
            "due_date",
            "completed_at",
            "comment_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["reporter", "completed_at", "comment_count"]

    def get_attachment_url(self, obj):
        if not obj.attachment:
            return ""
        try:
            return obj.attachment.url
        except ValueError:
            return ""


class TaskCommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = TaskComment
        fields = ["id", "task", "user", "comment", "created_at", "updated_at"]
        read_only_fields = ["task", "user"]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["id", "title", "message", "level", "link", "is_read", "created_at"]
