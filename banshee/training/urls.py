from django.urls import path
from .views import *

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("plan", TrainingCalView.as_view(), name="plan-total"),
    path("dashboard", DashboardView.as_view(), name="dashboard")
]
