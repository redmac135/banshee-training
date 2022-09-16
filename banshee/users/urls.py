from django.urls import path, include

from .views import *

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/officer", OfficerSignupView.as_view(), name="officer-signup"),
    path("login/", SigninView.as_view(), name="login"),
    path("settings", SettingsView.as_view(), name="settings"),
    path("", include("django.contrib.auth.urls")),
]
