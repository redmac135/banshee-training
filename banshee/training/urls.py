from django.urls import path
from .views import *

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("plan", TrainingNightView.as_view(), name="trainingnight"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path(
        "teach/<int:night_id>/<int:form_id>", TeachFormView.as_view(), name="teach-form"
    ),
    path("example", ExampleView.as_view(), name="example"),
]
