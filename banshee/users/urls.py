from django.urls import path, include
from .views import *

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("", include('django.contrib.auth.urls'))
]
