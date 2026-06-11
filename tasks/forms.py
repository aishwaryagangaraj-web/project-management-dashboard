from django import forms

from projects.models import Project

from .models import Task


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["project", "title", "description", "assignee", "status", "priority", "estimate_hours", "due_date"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields["project"].queryset = (
                Project.objects.filter(owner=user) | Project.objects.filter(members=user)
            ).distinct()

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date and due_date < Task.today():
            raise forms.ValidationError("Task due date cannot be before today.")
        return due_date
