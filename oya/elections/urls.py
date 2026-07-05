"""
URL patterns for elections app.
"""
from django.urls import path
from . import views

app_name = "elections"

urlpatterns = [
    path("", views.election_list, name="election_list"),
    path("create/", views.election_create, name="election_create"),
    path("<int:pk>/", views.election_detail, name="election_detail"),
    path("<int:pk>/update/", views.election_update, name="election_update"),
    path("candidates/create/", views.candidate_create, name="candidate_create"),
    path("candidates/<int:pk>/update/", views.candidate_update, name="candidate_update"),
    path("handovers/", views.handover_list, name="handover_list"),
    path("handovers/create/", views.handover_create, name="handover_create"),
]
