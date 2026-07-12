from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.permissions import IsAdminRole
from .models import Application
from .serializers import ApplicationSerializer, ApplicationStatusUpdateSerializer


class ApplicationViewSet(viewsets.ModelViewSet):
    """
    /api/applications/            GET (own applications, or all for admins), POST (submit new)
    /api/applications/<id>/       GET/PUT/PATCH/DELETE
    /api/applications/<id>/status/  PATCH (admin only) - move through Pending -> Under Review -> Approved/Rejected
    """

    serializer_class = ApplicationSerializer
    from common.permissions import IsOwnerOrAdmin
    permission_classes = (IsAuthenticated, IsOwnerOrAdmin)
    owner_field = "applicant"

    def get_queryset(self):
        user = self.request.user
        qs = Application.objects.select_related("applicant", "scheme")
        if user.is_staff or getattr(user, "role", None) == "admin":
            scheme_id = self.request.query_params.get("scheme")
            status_ = self.request.query_params.get("status")
            if scheme_id:
                qs = qs.filter(scheme_id=scheme_id)
            if status_:
                qs = qs.filter(status=status_)
            return qs
        return qs.filter(applicant=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        application = serializer.save()
        return Response(
            {
                "message": "Application submitted successfully.",
                "application": ApplicationSerializer(application, context=self.get_serializer_context()).data,
                "application_id": application.application_number,
            },
            status=201,
        )

    @action(detail=True, methods=["patch"], permission_classes=[IsAuthenticated, IsAdminRole])
    def status(self, request, pk=None):
        application = self.get_object()
        serializer = ApplicationStatusUpdateSerializer(application, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ApplicationSerializer(application).data)
