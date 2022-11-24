from django.urls import path, include
from django.contrib.auth.views import PasswordResetView

from .views import *

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", SigninView.as_view(), name="login"),
    path("settings", SettingsView.as_view(), name="settings"),
    path("training/settings", TrainingSettingsView.as_view(), name="trainingsettings"),
    path(
        "training/authusername", AuthorizedEmailFormView.as_view(), name="authusername"
    ),
    path(
        "training/authusername/<int:pk>",
        AuthorizedEmailDetailView.as_view(),
        name="authusername-detail",
    ),
    path("", include("django.contrib.auth.urls")),
]
