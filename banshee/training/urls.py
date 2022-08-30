from django.urls import path, register_converter
from .converters import DateConverter
from .views import *

register_converter(DateConverter, "date")

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("plan/<int:night_id>", TrainingNightView.as_view(), name="trainingnight"),
    path("dashboard/create", CreateDashboardView.as_view(), name="create-dashboard"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path(
        "teach/<int:night_id>/<int:form_id>", TeachFormView.as_view(), name="teach-form"
    ),
    path(
        "api/<int:year>/<int:month>/<int:day>",
        CreateTrainingNightView.as_view(),
        name="api-createtrainingnight",
    ),
    path("example", ExampleView.as_view(), name="example"),
]
