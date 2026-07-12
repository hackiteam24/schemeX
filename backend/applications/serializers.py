from rest_framework import serializers

from schemes.models import Scheme
from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    applicant_username = serializers.CharField(source="applicant.username", read_only=True)
    scheme_name = serializers.CharField(source="scheme.name", read_only=True)
    scheme = serializers.PrimaryKeyRelatedField(queryset=Scheme.objects.all())

    class Meta:
        model = Application
        fields = (
            "id",
            "applicant",
            "applicant_username",
            "scheme",
            "scheme_name",
            "application_number",
            "status",
            "submitted_date",
            "remarks",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "applicant", "application_number", "submitted_date", "status", "created_at", "updated_at")

    def validate(self, attrs):
        request = self.context.get("request")
        scheme = attrs.get("scheme")
        if request and scheme and Application.objects.filter(applicant=request.user, scheme=scheme).exists():
            raise serializers.ValidationError("You have already applied for this scheme.")
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["applicant"] = request.user
        return super().create(validated_data)


class ApplicationStatusUpdateSerializer(serializers.ModelSerializer):
    """Admin-only serializer for progressing an application's status."""

    class Meta:
        model = Application
        fields = ("status", "remarks")
