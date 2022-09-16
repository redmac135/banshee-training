from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import AuthorizedEmail
from .fields import CommaSeparatedEmailField
from training.models import Senior, Level


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )

    class Meta:
        fields = ["username", "password"]


class SignupForm(UserCreationForm):
    BLANK_CHOICE_RANK = [("", "Rank")]
    BLANK_CHOICE_LEVEL = [("", "Level")]
    BLANK_CHOICE_DASH = BLANK_CHOICE_DASH

    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "First Name"})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Last Name"})
    )
    email = forms.EmailField(widget=forms.EmailInput(attrs={"placeholder": "Email"}))
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"})
    )
    rank = forms.ChoiceField(
        choices=BLANK_CHOICE_RANK + BLANK_CHOICE_DASH + Senior.RANK_CHOICES
    )
    level = forms.ChoiceField(choices=BLANK_CHOICE_LEVEL + BLANK_CHOICE_DASH)

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)

        self.fields["level"].choices = (
            self.BLANK_CHOICE_LEVEL
            + self.BLANK_CHOICE_DASH
            + Level.get_senior_level_choices()
        )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "rank",
            "level",
            "password1",
            "password2",
        ]

    def check_email(email):
        return AuthorizedEmail.cadet_email_exists(email)

    def clean(self):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        if username and email:
            # Check Username and Email Uniqueness
            if User.objects.filter(username=username).exists():
                raise ValidationError(
                    {"username": "An Account with this Username Already Exists"}
                )
            if User.objects.filter(email=email).exists():
                raise ValidationError(
                    {"email": "An Account with this Email Already Exists"}
                )
            if not self.check_email(email):
                raise ValidationError({"email": "This email isn't authorized, if you believe this to be an error, please message the admin."})

        return cleaned_data

class OfficerSignupForm(SignupForm):
    rank = forms.ChoiceField(
        choices=Senior.OFFICER_RANK
    )

    def check_email(email):
        return AuthorizedEmail.officer_email_exists(email)

class AuthorizedEmailForm(forms.Form):
    is_officer = forms.BooleanField()
    emails = CommaSeparatedEmailField()

    class Meta:
        model = AuthorizedEmail
    
    def save(self):
        is_officer = self.cleaned_data.get("is_officer")
        emails = self.cleaned_data.get("emails")

        for email in emails:
            AuthorizedEmail.authorize_email(email, is_officer)