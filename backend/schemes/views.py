from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import Scheme
from .serializers import SchemeListSerializer, SchemeSerializer


class SchemeViewSet(viewsets.ModelViewSet):
    """
    /api/schemes/                 GET (list, filterable via ?category=&department=&state=&benefit=&search=&is_active=), POST (create)
    /api/schemes/<id>/            GET (retrieve), PUT/PATCH/DELETE
    Anyone authenticated can read; write access is enforced by IsAuthenticatedOrReadOnly
    at the view level and can be tightened to admins-only via common.permissions.ReadOnlyOrAdmin.
    """

    queryset = Scheme.objects.all()
    from common.permissions import ReadOnlyOrAdmin
    permission_classes = (ReadOnlyOrAdmin,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ("name", "category", "department", "description", "benefits", "state")
    ordering_fields = ("name", "last_updated", "created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return SchemeListSerializer
        return SchemeSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        for field in ("category", "department"):
            value = params.get(field)
            if value:
                qs = qs.filter(**{f"{field}__iexact": value})

        state = params.get("state")
        if state:
            from django.db.models import Q
            qs = qs.filter(Q(state__iexact=state) | Q(state__iexact="all"))

        benefit = params.get("benefit")
        if benefit:
            qs = qs.filter(benefits__icontains=benefit)

        is_active = params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ("1", "true", "yes"))
        return qs