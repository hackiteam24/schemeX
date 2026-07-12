from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminRole(BasePermission):
    """Allows access only to users with role=admin (or Django staff/superusers)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_staff or getattr(user, "role", None) == "admin")
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: the owning user (via `owner_field` on the view,
    defaults to "user") or an admin/staff user may access/modify the object.
    """

    owner_field = "user"

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff or getattr(user, "role", None) == "admin":
            return True
        owner_field = getattr(view, "owner_field", self.owner_field)
        owner = getattr(obj, owner_field, None)
        return owner == user


class ReadOnlyOrAdmin(BasePermission):
    """Anyone (including unauthenticated) can read; only admins can write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or getattr(request.user, "role", None) == "admin")
        )
