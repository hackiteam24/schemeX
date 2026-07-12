from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import get_dashboard_data


class DashboardStatsView(APIView):
    """GET /api/dashboard/ - aggregated dashboard data for the current user."""

    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(get_dashboard_data(request.user), status=status.HTTP_200_OK)
