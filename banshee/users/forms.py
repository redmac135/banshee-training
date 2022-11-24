from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
)
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages

from .fields import CommaSeparatedCharField
from .models import TrainingSetting, AuthorizedUsername
from training.models import Level


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )

    class Meta:
        fields = ["username", "password"]

    def clean(self):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(self.request, username=username, password=password)
            if user is None:
                raise ValidationError("Incorrect Username or Password")

        return cleaned_data


class SignupForm(UserCreationForm):
    BLANK_CHOICE_LEVEL = [("", "Level")]
    BLANK_CHOICE_DASH = BLANK_CHOICE_DASH

    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username"})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password"})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"})
    )
    level = forms.ChoiceField(choices=BLANK_CHOICE_LEVEL + BLANK_CHOICE_DASH)

    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)

        self.fields["level"].choices = (
            self.BLANK_CHOICE_LEVEL
            + self.BLANK_CHOICE_DASH
            + Level.seniors.get_choices()
        )

    class Meta:
        model = User
        fields = [
            "username",
            "level",
            "password1",
            "password2",
        ]

    def clean(self):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get("username")

        if username:
            # Check Username Uniqueness
            if User.objects.filter(username=username).exists():
                raise ValidationError(
                    {"username": "An account with this username already exists"}
                )
            if AuthorizedUsername.username_allowed(username) == False:
                raise ValidationError(
                    {
                        "username": "This Username is not authorized. Please contact the Admin if you believe this to be an error"
                    }
                )

        return cleaned_data


class UserSettingsForm(forms.Form):
    username = forms.CharField(
        max_length=191
    )  # https://docs.djangoproject.com/en/4.1/ref/contrib/auth/

    def __init__(self, user: User, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)

        self.instance = user

    def clean(self):
        currusername = self.instance.username
        cleaned_data = self.cleaned_data
        username = cleaned_data.get("username")

        if username:
            if (
                username != currusername
                and User.objects.filter(username=username).exists()
            ):
                raise ValidationError(
                    {"username": 'Username "%s" is not available.' % username}
                )

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        user_instance = self.instance

        user_instance.username = cleaned_data.get("username")
        user_instance.save()


class TrainingSettingsForm(forms.ModelForm):
    duedateoffset = forms.IntegerField(
        label="How many days before lessons are lesson plans due?"
    )
    allow_senior_assignment = forms.BooleanField(required=False)

    class Meta:
        model = TrainingSetting
        fields = ["duedateoffset", "allow_senior_assignment"]

    def text_fields(self):
        field_list = ["duedateoffset"]
        return [field for field in self if field.name in field_list]

    def boolean_fields(self):
        field_list = ["allow_senior_assignment"]
        return [field for field in self if field.name in field_list]

    def save(self, commit=True):
        cleaned_data = self.cleaned_data
        instance = TrainingSetting.create()
        instance.duedateoffset = cleaned_data.get("duedateoffset")
        instance.allow_senior_assignment = cleaned_data.get("allow_senior_assignment")
        instance.save()


class AuthorizedUsernameForm(forms.Form):
    usernames = CommaSeparatedCharField()

    def save(self, request):
        usernames = self.cleaned_data.get("usernames")

        for username in usernames:
            obj, created = AuthorizedUsername.authorize_username(username)
            if not created:
                messages.warning(
                    request,
                    "Username %s already exists and as been skipped." % str(obj),
                )
