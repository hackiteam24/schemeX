from django.conf import settings
from django.db import models

from common.models import TimeStampedUUIDModel


class ChatSession(TimeStampedUUIDModel):
    """A multi-turn conversation thread between a user and the AI assistant."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=255, default="New Chat")

    def __str__(self):
        return f"{self.title} ({self.id})"

    def preview(self):
        last_msg = self.messages.order_by("-created_at").first()
        return last_msg.content[:60] if last_msg else ""


class ChatMessage(TimeStampedUUIDModel):
    """A single message (from the user or the AI) inside a ChatSession."""

    SENDER_CHOICES = (
        ("user", "User"),
        ("ai", "AI"),
    )

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.sender}] {self.content[:40]}"


class AiChatHistory(TimeStampedUUIDModel):
    """
    Flat, queryable log of every user<->AI exchange, independent of the
    session/message thread structure above. Used for admin reporting and
    analytics (e.g. "what languages are people chatting in").
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="ai_chat_history",
    )
    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="history_entries",
        null=True,
        blank=True,
    )
    user_message = models.TextField()
    ai_response = models.TextField()
    language = models.CharField(max_length=5, default="en")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chatbots_aichathistory"
        ordering = ["-timestamp"]
        verbose_name = "AI Chat History"
        verbose_name_plural = "AI Chat History"
        indexes = [
            models.Index(fields=["language"]),
        ]

    def __str__(self):
        who = self.user.username if self.user else "Anonymous"
        return f"{who}: {self.user_message[:40]}"
