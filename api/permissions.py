from rest_framework import permissions


class IsFinancialSecretary(permissions.BasePermission):
    """Allow access to staff users (Financial Secretary / Superadmin)."""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)


class IsOwnerMember(permissions.BasePermission):
    """
    Allow a member to access only their own data.
    Staff can access any member's data.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        # obj may be a Member or an object with a .member FK
        member = getattr(obj, "member", obj)
        profile = getattr(request.user, "member_profile", None)
        return profile is not None and profile.pk == member.pk


class IsMemberOrStaff(permissions.BasePermission):
    """Authenticated member (read own) or staff (full access)."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
