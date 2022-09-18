from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.views.generic import View
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .tokens import account_activation_token
from .models import AccountActivation, AuthorizedEmail, TrainingSetting
from .forms import (
    OfficerSignupForm,
    ResendActivationEmailForm,
    SignupForm,
    LoginForm,
    AuthorizedEmailForm,
    TrainingSettingsForm,
    UserSettingsForm,
)
from training.models import Senior, Level


# Create your views here.
class SigninView(LoginView):
    template_name = "users/login.html"
    form_class = LoginForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(
            data=request.POST
        )  # Not sure why but it doesn't work if passed normal, must be a kwarg
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(username=username, password=password)
            login(request, user)

            # redirect user to home page
            messages.success(request, f"Welcome Back {str(user.senior)}!")
            return redirect("home")
        return render(request, self.template_name, {"form": form})


class SignupView(FormView):
    template_name = "users/signup.html"
    form_class = SignupForm

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        context["title"] = "Cadet Signup"
        return context

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        context = self.get_context_data()
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            user = form.save()

            level = form.cleaned_data.get("level")
            level_instance = Level.senior_numbertoinstance(level)
            rank = form.cleaned_data.get("rank")

            senior = Senior.objects.get_or_create(
                user=user, level=level_instance, rank=rank
            )
            user.save()
            AccountActivation.send_activation_email(user, request)
            messages.info(
                request,
                "Activation Email Sent, please activate your email before signing in",
            )

            # redirect user to home page
            return redirect("home")
        context = self.get_context_data()
        context.update(
            {"form": form}
        )  # override formclass from get_context_data as it doesn't contain request.POST data
        return render(request, self.template_name, {"form": form})


class OfficerSignupView(SignupView):
    form_class = OfficerSignupForm

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        context["title"] = "Officer Signup"
        return context


class AuthorizedEmailFormView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "users/authorizedemailform.html"
    form_class = AuthorizedEmailForm

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def form_valid(self, form):
        if form.has_changed():
            # form.save method was expanded to include request for messaging
            form.save(self.request)
            messages.success(self.request, "Emails Added Successfully.")
        return redirect("authemail")


class AuthorizedEmailDetailView(LoginRequiredMixin, UserPassesTestMixin, APIView):
    http_method_names = ["delete"]

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def delete(self, request, pk, *args, **kwargs):
        AuthorizedEmail.unauthorize_pk(pk)
        messages.success(request, f"Object Deleted")
        return Response(status.HTTP_200_OK)


class SettingsView(LoginRequiredMixin, FormView):
    template_name = "users/settings.html"
    form_class = UserSettingsForm

    def get_initial(self):
        initial = super(SettingsView, self).get_initial()
        initial["email"] = self.request.user.email
        initial["first_name"] = self.request.user.first_name
        initial["last_name"] = self.request.user.last_name
        initial["username"] = self.request.user.username
        initial["rank"] = Senior.rank_to_str(self.request.user.senior.rank)
        initial["level"] = self.request.user.senior.level

        return initial

    def get_form_kwargs(self):
        kwargs = super(SettingsView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        if form.has_changed():
            form.save()
            messages.success(self.request, "User Updated Successfully")
        return redirect("settings")


class TrainingSettingsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = "users/trainingsettings.html"
    form_class = TrainingSettingsForm

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def get_initial(self):
        initial = super(TrainingSettingsView, self).get_initial()
        initial["duedateoffset"] = TrainingSetting.get_duedateoffset()
        return initial

    def form_valid(self, form):
        if form.has_changed():
            form.save()
            messages.success(self.request, "Setting Updated Successfully")
        return redirect("trainingsettings")

    def get_context_data(self, **kwargs):
        context = super(TrainingSettingsView, self).get_context_data(**kwargs)
        context["authorizedemails"] = AuthorizedEmail.get_list_of_emails()
        return context


class ResendActivationEmailView(View):
    form_class = ResendActivationEmailForm
    template_name = "users/resend_activation_email.html"

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            email = cleaned_data.get("email")

            user = User.objects.get(email=email)

            AccountActivation.send_activation_email(user, request)
            messages.success(request, ("Activation Email Successfully Sent."))

            return redirect("login")

        return render(request, self.template_name, {"form": form})


class ActivateAccountView(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.senior.email_confirmed = True
            user.senior.save()
            messages.success(request, ("Your account have been confirmed."))
        else:
            messages.warning(
                request,
                (
                    "The confirmation link was invalid, possibly because it has already been used."
                ),
            )
        return redirect("login")
