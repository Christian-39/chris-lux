"""
Reviews URL configuration.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('add/<slug:product_slug>/', views.add_review, name='add_review'),
    path('edit/<int:review_id>/', views.edit_review, name='edit_review'),
    path('delete/<int:review_id>/', views.delete_review, name='delete_review'),
    path('helpful/', views.mark_helpful, name='mark_helpful'),
]
