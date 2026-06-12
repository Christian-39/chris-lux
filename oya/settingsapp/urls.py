"""
URL patterns for settingsapp.
"""
from django.urls import path
from . import views

app_name = "settingsapp"

urlpatterns = [
    path("", views.settings_view, name="settings"),
]
