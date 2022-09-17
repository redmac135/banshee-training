from django.urls import path, register_converter
from .converters import DateConverter
from .views import *

register_converter(DateConverter, "date")

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("plan/<int:night_id>", TrainingNightView.as_view(), name="trainingnight"),
    path(
        "plan/edit/<int:night_id>",
        EditTrainingNightView.as_view(),
        name="edit-trainingnight",
    ),
    path("plan/assign/<int:night_id>", AssignNightView.as_view(), name="night-assign"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("dashboard/<str:view>", DashboardView.as_view(), name="dashboard"),
    path(
        "teach/edit/<int:night_id>/<int:form_id>",
        TeachFormView.as_view(),
        name="teach-form",
    ),
    path(
        "teach/edit/<int:night_id>/<int:form_id>/<int:teach_id>",
        TeachFormView.as_view(),
        name="teach-form",
    ),
    path("teach/assign/<int:teach_id>", AssignTeachView.as_view(), name="teach-assign"),
    path("teach/<int:teach_id>", TeachView.as_view(), name="teach"),
    path(
        "api/<int:year>/<int:month>/<int:day>/",
        TrainingNightDetailView.as_view(),
        name="api-trainingnight",
    ),
    path("example", ExampleView.as_view(), name="example"),
]
