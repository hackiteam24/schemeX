from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """
    /api/notifications/                GET (own notifications), POST (admin/system create)
    /api/notifications/<id>/           GET/PATCH/DELETE
    /api/notifications/<id>/mark_read/ PATCH -> marks a single notification as read
    /api/notifications/mark_all_read/  PATCH -> marks every notification for the user as read
    """

    serializer_class = NotificationSerializer
    from common.permissions import IsOwnerOrAdmin
    permission_classes = (IsAuthenticated, IsOwnerOrAdmin)

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["patch"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read", "updated_at"])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=["patch"])
    def mark_all_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"message": f"{updated} notification(s) marked as read."})
