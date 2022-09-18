from django.urls import path, include

from .views import *

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/officer", OfficerSignupView.as_view(), name="officer-signup"),
    path("login/", SigninView.as_view(), name="login"),
    path("settings", SettingsView.as_view(), name="settings"),
    path("training/settings", TrainingSettingsView.as_view(), name="trainingsettings"),
    path("training/authemails", AuthorizedEmailFormView.as_view(), name="authemail"),
    path(
        "allowedemails/<int:pk>",
        AuthorizedEmailDetailView.as_view(),
        name="authemail-detail",
    ),
    path("activate/<uidb64>/<token>/", ActivateAccountView.as_view(), name="activate"),
    path("activation", ResendActivationEmailView.as_view(), name="resend-activation"),
    path("", include("django.contrib.auth.urls")),
]
