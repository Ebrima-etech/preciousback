from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_staff_user(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


class IsStaff(BasePermission):
    """Only staff/superusers."""

    def has_permission(self, request, view):
        return is_staff_user(request.user)


class IsStaffOrReadOnly(BasePermission):
    """Anyone can read; only staff/superusers can write."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return is_staff_user(request.user)
