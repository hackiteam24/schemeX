from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "gender", "district", "state", "pincode", "updated_at")
    list_filter = ("gender", "state", "district")
    search_fields = ("full_name", "user__username", "user__email", "pincode", "district", "state")
    readonly_fields = ("id", "created_at", "updated_at")
    autocomplete_fields = ("user",)
