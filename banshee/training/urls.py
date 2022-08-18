from django.urls import path
from .views import *

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("plan", TrainingNightView.as_view(), name="trainingnight"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("example", ExampleView.as_view(), name="example")
]
