from django.conf import settings
from django.db import models

from common.models import TimeStampedUUIDModel
from schemes.models import Scheme


class EligibilityCheck(TimeStampedUUIDModel):
    """Records the result of a user checking their eligibility for a scheme."""

    class Result(models.TextChoices):
        ELIGIBLE = "eligible", "Eligible"
        NOT_ELIGIBLE = "not_eligible", "Not Eligible"
        NEEDS_REVIEW = "needs_review", "Needs Manual Review"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="eligibility_checks",
    )
    scheme = models.ForeignKey(
        Scheme,
        on_delete=models.CASCADE,
        related_name="eligibility_checks",
    )
    eligibility_result = models.CharField(max_length=20, choices=Result.choices)
    reason = models.TextField(blank=True)
    checked_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "eligibility_eligibilitycheck"
        ordering = ["-checked_date"]
        indexes = [
            models.Index(fields=["eligibility_result"]),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.scheme.name} - {self.eligibility_result}"
