from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import AvatarUploadSerializer, ProfileSerializer
from .services import get_completion_status

PROFILE_FIELDS = {
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
}
USER_FIELDS = {"email", "phone_number", "preferred_language", "first_name", "last_name"}

FIELD_MAP = {
    "firstName": "first_name",
    "lastName": "last_name",
    "dateOfBirth": "date_of_birth",
    "maritalStatus": "marital_status",
    "aadhaarNumber": "aadhaar_number",
    "alternateMobile": "alternate_mobile",
    "annualIncome": "annual_income",
    "incomeSource": "income_source",
    "bplStatus": "bpl_status",
    "bankName": "bank_name",
    "accountNumber": "account_number",
    "ifscCode": "ifsc_code",
    "accountType": "account_type",
    "ownsLand": "owns_land",
    "landArea": "land_area",
    "landType": "land_type",
    "language": "preferred_language",
    "mobile": "phone_number",
}


class ProfileView(APIView):
    """
    GET  /api/profile/         -> full profile, grouped into UI sections
    PUT  /api/profile/<section>/ -> partially update whichever known fields
                                     are present in the payload (section name
                                     itself is informational only)
    """

    permission_classes = (IsAuthenticated,)

    def _get_profile(self, user):
        profile, _ = Profile.objects.get_or_create(
            user=user, defaults={"full_name": user.get_full_name() or user.username}
        )
        return profile

    def get(self, request):
        profile = self._get_profile(request.user)
        data = ProfileSerializer(profile, context={"request": request}).data
        avatar_url = request.build_absolute_uri(profile.profile_photo.url) if profile.profile_photo else None
        completion = get_completion_status(request.user, profile)

        return Response(
            {
                "avatar": avatar_url,
                "personal": {
                    "firstName": request.user.first_name,
                    "lastName": request.user.last_name,
                    "dateOfBirth": profile.date_of_birth,
                    "gender": profile.gender,
                    "category": profile.category,
                    "maritalStatus": profile.marital_status,
                    "aadhaarNumber": profile.aadhaar_number,
                },
                "contact": {
                    "email": request.user.email,
                    "mobile": request.user.phone_number,
                    "alternateMobile": profile.alternate_mobile,
                },
                "location": {
                    "address": profile.address,
                    "district": profile.district,
                    "state": profile.state,
                    "tehsil": profile.tehsil,
                    "village": profile.village,
                    "pincode": profile.pincode,
                },
                "economic": {
                    "annualIncome": profile.annual_income,
                    "incomeSource": profile.income_source,
                    "bplStatus": profile.bpl_status,
                    "occupation": profile.occupation,
                    "ownsLand": profile.owns_land,
                    "landArea": str(profile.land_area),
                    "landType": profile.land_type,
                },
                "bank": {
                    "bankName": profile.bank_name,
                    "accountNumber": profile.account_number,
                    "ifscCode": profile.ifsc_code,
                    "accountType": profile.account_type,
                },
                "preferences": {
                    "language": request.user.preferred_language,
                },
                "completion": completion,
                "profile": data,
            }
        )

    def put(self, request, section=None):
        profile = self._get_profile(request.user)
        user = request.user
        updated_fields = []

        for key, value in request.data.items():
            mapped_key = FIELD_MAP.get(key, key)
            
            # Clean/parse values to prevent database constraint errors
            if mapped_key == "date_of_birth" and value == "":
                value = None
            elif mapped_key == "annual_income":
                value = int(value) if value else 0
            elif mapped_key == "land_area":
                value = float(value) if value else 0.0

            if mapped_key in PROFILE_FIELDS:
                setattr(profile, mapped_key, value)
                updated_fields.append(mapped_key)
            elif mapped_key in USER_FIELDS:
                setattr(user, mapped_key, value)
                updated_fields.append(mapped_key)

        # Handle updating full_name if first_name/last_name changes
        if "first_name" in updated_fields or "last_name" in updated_fields:
            profile.full_name = f"{user.first_name} {user.last_name}".strip() or user.username
            profile.save()

        if any(f in USER_FIELDS for f in updated_fields):
            user.save()
        profile.save()

        completion = get_completion_status(user, profile)

        return Response(
            {
                "message": "Changes saved successfully.",
                "profile": ProfileSerializer(profile, context={"request": request}).data,
                "completion": completion,
            }
        )


class AvatarUploadView(APIView):
    """POST /api/profile/avatar/ - multipart upload of the profile photo."""

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        profile, _ = Profile.objects.get_or_create(
            user=request.user, defaults={"full_name": request.user.get_full_name() or request.user.username}
        )
        serializer = AvatarUploadSerializer(profile, data={"profile_photo": request.data.get("avatar")})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                "message": "Avatar updated successfully.",
                "avatar_url": request.build_absolute_uri(profile.profile_photo.url),
            }
        )


class AdminProfileListView(APIView):
    """GET /api/profile/admin/users/ - get all registered users and their profiles (Admin only)."""
    
    def get(self, request):
        from common.permissions import IsAdminRole
        # Enforce IsAdminRole programmatically or via permission_classes
        permission = IsAdminRole()
        if not permission.has_permission(request, self):
            return Response({"message": "Not authorized."}, status=status.HTTP_403_FORBIDDEN)

        from accounts.models import User
        users = User.objects.select_related("profile").all()
        data = []
        for u in users:
            profile_data = {}
            if hasattr(u, "profile"):
                profile_data = {
                    "full_name": u.profile.full_name,
                    "gender": u.profile.gender,
                    "date_of_birth": u.profile.date_of_birth,
                    "category": u.profile.category,
                    "marital_status": u.profile.marital_status,
                    "alternate_mobile": u.profile.alternate_mobile,
                    "address": u.profile.address,
                    "district": u.profile.district,
                    "state": u.profile.state,
                    "tehsil": u.profile.tehsil,
                    "village": u.profile.village,
                    "pincode": u.profile.pincode,
                    "annual_income": u.profile.annual_income,
                    "income_source": u.profile.income_source,
                    "bpl_status": u.profile.bpl_status,
                    "occupation": u.profile.occupation,
                    "owns_land": u.profile.owns_land,
                    "land_area": str(u.profile.land_area),
                    "land_type": u.profile.land_type,
                    "bank_name": u.profile.bank_name,
                    "account_number": u.profile.account_number,
                    "ifsc_code": u.profile.ifsc_code,
                    "account_type": u.profile.account_type,
                }
            data.append({
                "id": str(u.id),
                "username": u.username,
                "email": u.email,
                "phone_number": u.phone_number,
                "role": u.role,
                "is_active": u.is_active,
                "date_joined": u.date_joined,
                "profile": profile_data
            })
        return Response(data)
