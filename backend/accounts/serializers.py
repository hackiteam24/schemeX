from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Read/update serializer for the authenticated user's own account."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone_number",
            "preferred_language",
            "role",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
        )
        read_only_fields = ("id", "role", "date_joined", "last_login")


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles POST /api/auth/register/.

    Accepts the payload sent by frontend/static/js/auth.js:
    { username, mobile, email, password, first_name, last_name, language }
    """

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    email = serializers.EmailField(required=True)
    mobile = serializers.CharField(source="phone_number", required=False, allow_blank=True)
    language = serializers.ChoiceField(
        source="preferred_language",
        choices=User.Language.choices,
        required=False,
        allow_blank=True,
        default=User.Language.ENGLISH,
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "mobile",
            "first_name",
            "last_name",
            "language",
        )

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_language(self, value):
        # Frontend sends "" when no language has been explicitly selected yet.
        # allow_blank lets that through this far; treat it as "not provided"
        # rather than a real choice.
        return value or User.Language.ENGLISH

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def validate_mobile(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """
    Handles POST /api/auth/login/.

    Returns the shape expected by frontend/static/js/auth.js:
    { user: { ...profile fields..., token } }
    """

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        if not user.is_active:
            raise serializers.ValidationError("This account has been deactivated.")
        attrs["user"] = user
        return attrs

    def to_representation(self, instance):
        user = instance["user"]
        refresh = RefreshToken.for_user(user)
        data = UserSerializer(user).data
        data["token"] = str(refresh.access_token)
        data["refresh"] = str(refresh)
        return {"user": data}