from rest_framework import serializers

from schemes.models import Scheme
from .models import EligibilityCheck


class EligibilityCheckSerializer(serializers.ModelSerializer):
    scheme_name = serializers.CharField(source="scheme.name", read_only=True)
    scheme = serializers.PrimaryKeyRelatedField(queryset=Scheme.objects.all())

    class Meta:
        model = EligibilityCheck
        fields = (
            "id",
            "user",
            "scheme",
            "scheme_name",
            "eligibility_result",
            "reason",
            "checked_date",
            "created_at",
        )
        read_only_fields = ("id", "user", "eligibility_result", "reason", "checked_date", "created_at")


class EligibilityCheckRequestSerializer(serializers.Serializer):
    """Input payload for POST /api/eligibility/check/."""

    scheme = serializers.PrimaryKeyRelatedField(queryset=Scheme.objects.all())
    answers = serializers.DictField(required=False, default=dict)
