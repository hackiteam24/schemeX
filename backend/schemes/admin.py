from django.contrib import admin

from .models import Scheme


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "department", "is_active", "last_updated")
    list_filter = ("category", "department", "is_active")
    search_fields = ("name", "category", "department", "description")
    readonly_fields = ("id", "last_updated", "created_at", "updated_at")
    prepopulated_fields = {}
