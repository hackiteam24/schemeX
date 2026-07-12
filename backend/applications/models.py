import random
import string

from django.conf import settings
from django.db import models

from common.models import TimeStampedUUIDModel
from schemes.models import Scheme


def generate_application_number():
    prefix = "SX"
    suffix = "".join(random.choices(string.digits, k=10))
    return f"{prefix}{suffix}"


class Application(TimeStampedUUIDModel):
    """A citizen's application to a government scheme."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        UNDER_REVIEW = "under_review", "Under Review"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="applications",
    )
    application_number = models.CharField(
        max_length=20,
        unique=True,
        default=generate_application_number,
        editable=False,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    submitted_date = models.DateTimeField(auto_now_add=True)
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = "applications_application"
        ordering = ["-submitted_date"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["application_number"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["applicant", "scheme"], name="unique_applicant_scheme")
        ]

    def __str__(self):
        return f"{self.application_number} - {self.applicant.username} - {self.scheme.name}"
