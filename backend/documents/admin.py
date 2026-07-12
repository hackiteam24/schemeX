from django.contrib import admin

from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("document_type", "uploaded_by", "application", "verification_status", "upload_date")
    list_filter = ("document_type", "verification_status")
    search_fields = ("uploaded_by__username", "uploaded_by__email", "document_type")
    readonly_fields = ("id", "upload_date", "created_at", "updated_at")
    autocomplete_fields = ("uploaded_by", "application")
    date_hierarchy = "upload_date"
