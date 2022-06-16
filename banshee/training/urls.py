from django.urls import path
from .views import *

urlpatterns = [
    path('signup', HomeView.as_view(), name='home')
]