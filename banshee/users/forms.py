from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from training.models import Senior, Level


class SignupForm(UserCreationForm):
    rank = forms.ChoiceField(choices=Senior.RANK_CHOICES)
    level = forms.ChoiceField(choices=Level.get_senior_choices())

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

        return cleaned_data
