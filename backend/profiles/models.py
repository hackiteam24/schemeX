from django.conf import settings
from django.db import models

from common.models import TimeStampedUUIDModel


def profile_photo_path(instance, filename):
    return f"profile_photos/{instance.user_id}/{filename}"


class Profile(TimeStampedUUIDModel):
    """Extended demographic/address details for a citizen (1:1 with User)."""

    class Gender(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=20, blank=True)
    marital_status = models.CharField(max_length=20, blank=True)
    aadhaar_number = models.CharField(max_length=12, blank=True)
    
    # Contact Details
    alternate_mobile = models.CharField(max_length=15, blank=True)
    
    # Location Details
    address = models.TextField(blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    tehsil = models.CharField(max_length=100, blank=True)
    village = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=6, blank=True)
    
    # Economic Details
    annual_income = models.IntegerField(default=0, blank=True)
    income_source = models.CharField(max_length=50, blank=True)
    bpl_status = models.CharField(max_length=10, blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    owns_land = models.CharField(max_length=10, blank=True)
    land_area = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True)
    land_type = models.CharField(max_length=50, blank=True)
    
    # Bank Details
    bank_name = models.CharField(max_length=150, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    ifsc_code = models.CharField(max_length=20, blank=True)
    account_type = models.CharField(max_length=20, blank=True)
    
    profile_photo = models.ImageField(upload_to=profile_photo_path, null=True, blank=True)

    class Meta:
        db_table = "profiles_profile"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["district", "state"]),
            models.Index(fields=["pincode"]),
        ]

    def __str__(self):
        return f"Profile of {self.user.username}"
