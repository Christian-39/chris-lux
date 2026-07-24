"""
URL patterns for OYA Project Donations.
"""
from django.urls import path
from . import views

app_name = "project_donations"

urlpatterns = [
    # Outside Donors
    path("outside-donors/", views.outside_donor_list, name="outside_donor_list"),
    path("outside-donors/create/", views.outside_donor_create, name="outside_donor_create"),
    path("outside-donors/<int:pk>/", views.outside_donor_detail, name="outside_donor_detail"),
    path("outside-donors/<int:pk>/update/", views.outside_donor_update, name="outside_donor_update"),
    path("outside-donors/<int:pk>/delete/", views.outside_donor_delete, name="outside_donor_delete"),

    # Donations
    path("donations/", views.donation_list, name="donation_list"),
    path("donations/create/", views.donation_create, name="donation_create"),
    path("donations/<int:pk>/", views.donation_detail, name="donation_detail"),
    path("donations/<int:pk>/update/", views.donation_update, name="donation_update"),
    path("donations/<int:pk>/delete/", views.donation_delete, name="donation_delete"),

    # Reports
    path("reports/project/<int:project_id>/", views.project_fundraising_report, name="project_fundraising_report"),
    path("reports/outside-donor/<int:pk>/", views.outside_donor_statement_pdf, name="outside_donor_statement"),
    path("reports/member/<int:pk>/", views.member_donation_history_pdf, name="member_donation_history"),
    path("reports/history/", views.donation_history_report, name="donation_history_report"),

    # AJAX
    path("api/search-outside-donors/", views.search_outside_donors_ajax, name="search_outside_donors_ajax"),
    path("api/donor-inviter/", views.get_outside_donor_inviter_ajax, name="get_donor_inviter_ajax"),
]
