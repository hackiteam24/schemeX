from django.contrib import admin

from .models import EligibilityCheck


@admin.register(EligibilityCheck)
class EligibilityCheckAdmin(admin.ModelAdmin):
    list_display = ("user", "scheme", "eligibility_result", "checked_date")
    list_filter = ("eligibility_result", "scheme")
    search_fields = ("user__username", "user__email", "scheme__name")
    readonly_fields = ("id", "checked_date", "created_at", "updated_at")
    autocomplete_fields = ("user", "scheme")
    date_hierarchy = "checked_date"
