from django.urls import path, include
from django.contrib.auth.views import PasswordResetView

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
    path("password_reset", PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", PasswordResetRedirectView.as_view(), name="password_reset_done"),
    path("reset/done/", PasswordResetCompleteRedirectView.as_view(), name="password_reset_complete"),
    path('', include('django.contrib.auth.urls'))
]
