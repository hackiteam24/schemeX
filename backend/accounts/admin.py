from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin configuration for the custom User model."""

    ordering = ["-date_joined"]
    list_display = (
        "username",
        "email",
        "phone_number",
        "role",
        "preferred_language",
        "is_active",
        "date_joined",
        "last_login",
    )
    list_filter = ("role", "preferred_language", "is_active", "is_staff", "date_joined")
    search_fields = ("username", "email", "phone_number", "first_name", "last_name")
    readonly_fields = ("id", "date_joined", "last_login", "created_at", "updated_at")

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "SchemeX Profile",
            {"fields": ("phone_number", "preferred_language", "role")},
        ),
        ("Audit", {"fields": ("id", "created_at", "updated_at")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (
            "SchemeX Profile",
            {"fields": ("email", "phone_number", "preferred_language", "role")},
        ),
    )
