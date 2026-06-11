from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profile


class CleanAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "The username or password you entered is incorrect.",
        "inactive": "This account is inactive.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "placeholder": "Enter your username"}
        )
        self.fields["password"].widget.attrs.update(
            {"autocomplete": "current-password", "placeholder": "Enter your password"}
        )


class RegisterForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"autocomplete": "username", "placeholder": "Choose a username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Create a password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"autocomplete": "new-password", "placeholder": "Confirm your password"}
        )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["avatar", "department", "phone"]
        widgets = {
            "department": forms.TextInput(attrs={"placeholder": "Department"}),
            "phone": forms.TextInput(attrs={"placeholder": "Phone"}),
        }
