from django.urls import path, include
from django.contrib.auth.views import PasswordResetView

from .views import *

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", SigninView.as_view(), name="login"),
    path("settings", SettingsView.as_view(), name="settings"),
    path("training/settings", TrainingSettingsView.as_view(), name="trainingsettings"),
    path("", include("django.contrib.auth.urls")),
]
