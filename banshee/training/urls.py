from django.urls import path, register_converter
from .converters import DateConverter
from .views import *

register_converter(DateConverter, "date")

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("plan/<int:night_id>", TrainingNightView.as_view(), name="trainingnight"),
    path("dashboard/<str:view>", DashboardView.as_view(), name="dashboard"),
    path(
        "teach/edit/<int:night_id>/<int:form_id>",
        TeachFormView.as_view(),
        name="teach-form",
    ),
    path("teach/assign/<int:teach_id>", AssignSeniorView.as_view(), name="teach-assign"),
    path("teach/<int:teachid>", TeachView.as_view(), name="teach"),
    path(
        "api/<int:year>/<int:month>/<int:day>/",
        EditTrainingNightView.as_view(),
        name="api-trainingnight",
    ),
    path("example/<int:teach_id>", AssignSeniorView.as_view(), name="example"),
]
