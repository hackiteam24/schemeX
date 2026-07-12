from django.conf import settings
from django.db import models

from common.models import TimeStampedUUIDModel


class Notification(TimeStampedUUIDModel):
    """An in-app notification sent to a user (application updates, reminders, etc.)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notification"
        ordering = ["-created_time"]
        indexes = [
            models.Index(fields=["is_read"]),
        ]

    def __str__(self):
        return f"{self.title} -> {self.user.username}"
