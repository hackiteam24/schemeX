from rest_framework import serializers

from .models import Profile


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    phone_number = serializers.CharField(source="user.phone_number", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "email",
            "phone_number",
            "full_name",
            "gender",
            "date_of_birth",
            "category",
            "marital_status",
            "aadhaar_number",
            "alternate_mobile",
            "address",
            "district",
            "state",
            "tehsil",
            "village",
            "pincode",
            "annual_income",
            "income_source",
            "bpl_status",
            "occupation",
            "owns_land",
            "land_area",
            "land_type",
            "bank_name",
            "account_number",
            "ifsc_code",
            "account_type",
            "profile_photo",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class AvatarUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("profile_photo",)

    def validate_profile_photo(self, value):
        import os
        from django.core.exceptions import ValidationError

        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise ValidationError("File size exceeds the 5MB limit.")

        ext = os.path.splitext(value.name)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png']
        if ext not in valid_extensions:
            raise ValidationError("Invalid file extension. Only JPG, JPEG, and PNG are allowed.")

        from django.utils.text import get_valid_filename
        value.name = get_valid_filename(os.path.basename(value.name))
        return value
