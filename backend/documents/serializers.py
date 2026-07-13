from rest_framework import serializers

from .models import Document


class DocumentSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(source="uploaded_by.username", read_only=True)
    document_type_display = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = (
            "id",
            "uploaded_by",
            "uploaded_by_username",
            "application",
            "document_type",
            "document_type_display",
            "file",
            "file_url",
            "verification_status",
            "rejection_reason",
            "upload_date",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "uploaded_by", "verification_status", "rejection_reason", "upload_date", "created_at", "updated_at")

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def get_document_type_display(self, obj):
        if obj.document_type == "other" and obj.file:
            name = obj.file.name.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
            clean_name = name.replace("_", " ").replace("-", " ").split(".")[0].title()
            if clean_name.lower().startswith("niffa "):
                clean_name = clean_name[6:]
            return clean_name
        return obj.get_document_type_display()

    def validate_file(self, value):
        import os
        from django.core.exceptions import ValidationError

        # Validate file size (max 5MB)
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise ValidationError("File size exceeds the 5MB limit.")

        # Validate file extension / mime type
        ext = os.path.splitext(value.name)[1].lower()
        valid_extensions = ['.pdf', '.jpg', '.jpeg', '.png']
        if ext not in valid_extensions:
            raise ValidationError("Invalid file extension. Only PDF, JPG, JPEG, and PNG are allowed.")

        # Path traversal mitigation: sanitize filename using Django utilities
        from django.utils.text import get_valid_filename
        value.name = get_valid_filename(os.path.basename(value.name))
        return value

    def create(self, validated_data):
        validated_data["uploaded_by"] = self.context["request"].user
        return super().create(validated_data)


class DocumentVerificationSerializer(serializers.ModelSerializer):
    """Admin-only serializer for verifying/rejecting an uploaded document."""

    class Meta:
        model = Document
        fields = ("verification_status", "rejection_reason")
