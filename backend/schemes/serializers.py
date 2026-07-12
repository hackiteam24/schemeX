from rest_framework import serializers

from .models import Scheme


class SchemeSerializer(serializers.ModelSerializer):
    required_documents_list = serializers.ListField(read_only=True)

    class Meta:
        model = Scheme
        fields = (
            "id",
            "name",
            "category",
            "department",
            "description",
            "benefits",
            "eligibility_criteria",
            "required_documents",
            "required_documents_list",
            "how_to_apply",
            "official_link",
            "is_active",
            "state",
            "min_age",
            "max_age",
            "gender_limit",
            "max_income",
            "bpl_required",
            "land_required",
            "caste_categories",
            "last_updated",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "last_updated", "created_at", "updated_at")


class SchemeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    required_documents_list = serializers.ListField(read_only=True)

    class Meta:
        model = Scheme
        fields = (
            "id",
            "name",
            "category",
            "department",
            "description",
            "benefits",
            "required_documents_list",
            "official_link",
            "is_active",
            "state",
            "min_age",
            "max_age",
            "gender_limit",
            "max_income",
            "bpl_required",
            "land_required",
            "caste_categories",
            "last_updated",
        )