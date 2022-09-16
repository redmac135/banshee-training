from django.urls import path, include

from .views import *

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("signup/officer", OfficerSignupView.as_view(), name="officer-signup"),
    path("login/", SigninView.as_view(), name="login"),
    path("allowedemails/<int:pk>", AuthorizedEmailDetailView.as_view(), name="authemail-detail"),
    path("", include("django.contrib.auth.urls")),
]
