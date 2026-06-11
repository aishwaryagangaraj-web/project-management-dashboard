from django import forms
from django.contrib.auth import get_user_model

from accounts.access import is_admin
from projects.models import Project

from .models import Task, TaskComment

User = get_user_model()


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [
            "project",
            "title",
            "description",
            "assignee",
            "status",
            "priority",
            "estimate_hours",
            "attachment",
            "due_date",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user is not None:
            if is_admin(user):
                self.fields["project"].queryset = Project.objects.all()
                self.fields["assignee"].queryset = User.objects.all()
            else:
                self.fields["project"].queryset = Project.objects.filter(owner=user).distinct()

        project = None
        if self.is_bound:
            project_id = self.data.get("project")
            if project_id:
                project = Project.objects.filter(pk=project_id).first()
        elif self.instance and self.instance.project_id:
            project = self.instance.project

        if project:
            assignees = User.objects.filter(pk=project.owner_id) | project.members.all()
            if user is not None and user.pk:
                assignees = assignees | User.objects.filter(pk=user.pk)
            self.fields["assignee"].queryset = assignees.distinct()
        elif user is not None and not is_admin(user):
            self.fields["assignee"].queryset = User.objects.filter(pk=user.pk)

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < Task.today():
            raise forms.ValidationError("Task due date cannot be before today.")
        return due_date


class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4, "placeholder": "Write a comment..."}),
        }
