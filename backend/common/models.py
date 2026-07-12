import uuid

from django.db import models


class TimeStampedUUIDModel(models.Model):
    """
    Abstract base model used across the project.

    Provides:
      - a UUID primary key (safer to expose in public APIs than sequential ints)
      - created_at / updated_at audit timestamps on every table
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID4) for this record.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]
