import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model for SchemeX.

    Extends Django's AbstractUser (keeps username/password/email/first_name/
    last_name/is_staff/is_active/date_joined/last_login/groups/permissions
    working out of the box) and adds the citizen-service specific fields
    required by the platform.
    """

    class Role(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        ADMIN = "admin", "Admin"

    class Language(models.TextChoices):
        ENGLISH = "en", "English"
        HINDI = "hi", "Hindi"
        TAMIL = "ta", "Tamil"
        TELUGU = "te", "Telugu"
        KANNADA = "kn", "Kannada"
        MALAYALAM = "ml", "Malayalam"
        BENGALI = "bn", "Bengali"
        MARATHI = "mr", "Marathi"
        GUJARATI = "gu", "Gujarati"
        PUNJABI = "pa", "Punjabi"
        ODIA = "or", "Odia"
        ASSAMESE = "as", "Assamese"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID4) for this user.",
    )
    email = models.EmailField("email address", unique=True)
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        null=True,
        blank=True,
        help_text="Mobile number used for OTP / notifications.",
    )
    preferred_language = models.CharField(
        max_length=5,
        choices=Language.choices,
        default=Language.ENGLISH,
    )
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.CITIZEN,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # date_joined and last_login already provided by AbstractUser/AbstractBaseUser.

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["phone_number"]),
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.username

    @property
    def is_admin_role(self):
        return self.role == self.Role.ADMIN
