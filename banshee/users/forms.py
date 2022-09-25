from django import forms
from django.db.models.fields import BLANK_CHOICE_DASH
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib import messages

from .models import AuthorizedEmail, TrainingSetting
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

    def clean(self):
        cleaned_data = self.cleaned_data
        username = cleaned_data.get("username")
        password = cleaned_data.get("password")

        if username and password:
            user = authenticate(self.request, username=username, password=password)
            if user is None:
                raise ValidationError("Incorrect Username or Password")
            if user.senior.email_confirmed == False:
                raise ValidationError("Activate your email before logging in.")

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
            + Level.seniors.get_choices()
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

    def check_email(self, email):
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
                raise ValidationError(
                    {
                        "email": "This email isn't authorized, if you believe this to be an error, please message the admin."
                    }
                )

        return cleaned_data


class OfficerSignupForm(SignupForm):
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)

        self.fields["rank"].initial = Senior.OFFICER_RANK_NUMBER
        self.fields["rank"].widget = forms.widgets.HiddenInput()
        self.fields["level"].initial = Level.OFFICER_LEVEL_NUMBER
        self.fields["level"].widget = forms.widgets.HiddenInput()

    def check_email(self, email):
        return AuthorizedEmail.officer_email_exists(email)


class UserSettingsForm(forms.Form):
    email = forms.EmailField()
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
    def settings_fields(self):
        field_list = ["email"]
        return [field for field in self if field.name in field_list]

    def active_fields(self):
        field_list = ["username", "first_name", "last_name"]
        return [field for field in self if field.name in field_list]

    def inactive_fields(self):
        field_list = ["level", "rank"]
        return [field for field in self if field.name in field_list]

    def clean(self):
        currusername = self.instance.username
        curremail = self.instance.email
        cleaned_data = self.cleaned_data
        username = cleaned_data.get("username")
        email = cleaned_data.get("email")

        if username and email:
            if (
                username != currusername
                and User.objects.filter(username=username).exists()
            ):
                raise ValidationError(
                    {"username": 'Username "%s" is not available.' % username}
                )
            if email != curremail and User.objects.filter(email=email).exists():
                raise ValidationError({"email": "Email already taken."})
            if not AuthorizedEmail.email_exists(email):
                raise ValidationError(
                    {
                        "email": "This email is not authorized, if you believe this to be an error, message the admin."
                    }
                )

        return cleaned_data

    def save(self):
        cleaned_data = self.cleaned_data
        user_instance = self.instance

        user_instance.email = cleaned_data.get("email")
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


class ResendActivationEmailForm(forms.Form):
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"placeholder": "Email"})
    )

    def clean(self):
        cleaned_data = self.cleaned_data
        email = cleaned_data.get("email")

        if email:
            if not User.objects.filter(email=email).exists():
                raise ValidationError(
                    {"email": "An Account with this Email Address does not Exist"}
                )
            user = User.objects.get(email=email)
            senior = Senior.objects.get(user=user)
            if senior.email_confirmed == True:
                raise ValidationError({"email": "Your Email is Already Active!"})

        return cleaned_data


class AuthorizedEmailForm(forms.Form):
    is_officer = forms.BooleanField(required=False)
    emails = CommaSeparatedEmailField()

    def save(self, request):
        is_officer = self.cleaned_data.get("is_officer")
        emails = self.cleaned_data.get("emails")

        for email in emails:
            obj, created = AuthorizedEmail.authorize_email(email, is_officer)
            if not created:
                messages.warning(
                    request, "Email %s already exists so has been skipped" % str(obj)
                )
