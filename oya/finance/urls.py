"""
URL patterns for finance app.
"""
from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("income/", views.income_list, name="income_list"),
    path("income/create/", views.income_create, name="income_create"),
    path("income/<int:pk>/", views.income_detail, name="income_detail"),
    path("income/<int:pk>/delete/", views.income_delete, name="income_delete"),
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/create/", views.expense_create, name="expense_create"),
    path("expenses/<int:pk>/", views.expense_detail, name="expense_detail"),
    path("expenses/<int:pk>/delete/", views.expense_delete, name="expense_delete"),
    path("summary/", views.finance_summary, name="finance_summary"),
    # AJAX endpoint
    path("api/search-members/", views.search_members, name="search_members"),
]