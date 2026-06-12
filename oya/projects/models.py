"""
Models for OYA projects.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import BaseModel


class Project(BaseModel):
    """Project model for tracking association projects."""

    STATUS_CHOICES = [
        ("FUTURE", "Future"),
        ("AT_HAND", "At Hand"),
        ("FINISHED", "Finished"),
    ]

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name="Title")
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name="Budget"
    )
    description = models.TextField(blank=True, verbose_name="Description")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="FUTURE",
        verbose_name="Status"
    )
    progress_percentage = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        verbose_name="Progress Percentage"
    )

    class Meta:
        db_table = "projects_project"
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["progress_percentage"]),
        ]

    def __str__(self):
        return self.title

    def is_future(self):
        return self.status == "FUTURE"

    def is_at_hand(self):
        return self.status == "AT_HAND"

    def is_finished(self):
        return self.status == "FINISHED"
