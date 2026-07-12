from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("application_number", "applicant", "scheme", "status", "submitted_date")
    list_filter = ("status", "scheme")
    search_fields = ("application_number", "applicant__username", "applicant__email", "scheme__name")
    readonly_fields = ("id", "application_number", "submitted_date", "created_at", "updated_at")
    autocomplete_fields = ("applicant", "scheme")
    date_hierarchy = "submitted_date"
