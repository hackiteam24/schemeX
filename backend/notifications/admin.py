from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "is_read", "created_time")
    list_filter = ("is_read", "created_time")
    search_fields = ("title", "message", "user__username", "user__email")
    readonly_fields = ("id", "created_time", "created_at", "updated_at")
    autocomplete_fields = ("user",)
    date_hierarchy = "created_time"
