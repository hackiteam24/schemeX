from django.contrib import admin

from .models import AiChatHistory, ChatMessage, ChatSession


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ("sender", "content", "created_at")


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "created_at", "updated_at")
    list_filter = ("created_at",)
    search_fields = ("title", "user__username", "user__email")
    inlines = [ChatMessageInline]
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(AiChatHistory)
class AiChatHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "language", "timestamp", "short_message")
    list_filter = ("language", "timestamp")
    search_fields = ("user__username", "user_message", "ai_response")
    readonly_fields = ("id", "timestamp", "created_at", "updated_at")
    date_hierarchy = "timestamp"

    def short_message(self, obj):
        return obj.user_message[:60]
    short_message.short_description = "User Message"
