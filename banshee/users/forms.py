from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.auth.forms import (
    UserCreationForm,
    AuthenticationForm,
)
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from .models import TrainingSetting
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
            + Level.seniors.get_choices()
        )

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "rank",
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
                    {"username": "An Account with this Username Already Exists"}
                )

        return cleaned_data


class UserSettingsForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()
    username = forms.CharField(
        max_length=191
    )  # https://docs.djangoproject.com/en/4.1/ref/contrib/auth/
    rank = forms.CharField(disabled=True)
    level = forms.CharField(disabled=True)

    def __init__(self, user: User, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)

        self.instance = user

    # Get methods for organizing fields in template
    def active_fields(self):
        field_list = ["username", "first_name", "last_name"]
        return [field for field in self if field.name in field_list]

    def inactive_fields(self):
        field_list = ["level", "rank"]
        return [field for field in self if field.name in field_list]

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

        user_instance.first_name = cleaned_data.get("first_name")
        user_instance.last_name = cleaned_data.get("last_name")
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
