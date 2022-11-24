from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from .models import TrainingSetting
from .forms import (
    SignupForm,
    LoginForm,
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
            return self.form_valid(form)
        context = self.get_context_data()
        context.update(
            {"form": form}
        )  # override formclass from get_context_data as it doesn't contain request.POST data
        return render(request, self.template_name, {"form": form})

    def form_valid(self, form):
        user = form.save()

        level = form.cleaned_data.get("level")
        level_instance = Level.levels.get_by_number(level)

        Senior.objects.get_or_create(user=user, level=level_instance)
        user.save()
        login(self.request, user)

        return redirect("dashboard")


class SettingsView(LoginRequiredMixin, FormView):
    template_name = "users/settings.html"
    form_class = UserSettingsForm

    def get_initial(self):
        initial = super(SettingsView, self).get_initial()
        initial["username"] = self.request.user.username
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
        initial["allow_senior_assignment"] = TrainingSetting.get_senior_assignment()
        return initial

    def form_valid(self, form):
        if form.has_changed():
            form.save()
            messages.success(self.request, "Setting Updated Successfully")
        return redirect("trainingsettings")

    def get_context_data(self, **kwargs):
        context = super(TrainingSettingsView, self).get_context_data(**kwargs)
        context["unassignable_seniors"] = Senior.seniors.get_unassignable_seniors()
        return context
