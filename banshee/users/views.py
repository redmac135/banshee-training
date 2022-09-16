from django.shortcuts import render, redirect
from django.views.generic.edit import FormView
from django.contrib.auth.views import LoginView
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AuthorizedEmail
from .forms import OfficerSignupForm, SignupForm, LoginForm, AuthorizedEmailForm
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
            return redirect("home")
        return render(request, self.template_name, {"form": form})


class SignupView(FormView):
    template_name = "users/signup.html"
    form_class = SignupForm

    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        form = self.form_class()
        return render(request, self.template_name, {"form": form})

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

            raw_password = form.cleaned_data.get("password1")

            # login user after signing up
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)

            # redirect user to home page
            return redirect("home")
        return render(request, self.template_name, {"form": form})


class OfficerSignupView(SignupView):
    form_class = OfficerSignupForm

class AuthorizedEmailFormView(FormView):
    template_name = "users/authorizedemailform.html"
    form_class = AuthorizedEmailForm

class AuthorizedEmailDetailView(LoginRequiredMixin, UserPassesTestMixin, APIView):
    http_method_names = ["delete"]

    # For UserPassesTestMixin
    def test_func(self):
        return self.request.user.senior.is_training()

    def delete(self, request, pk, *args, **kwargs):
        AuthorizedEmail.unauthorize_pk(pk)
        return Response(status.HTTP_200_OK)