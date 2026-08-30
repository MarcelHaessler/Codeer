from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProfileOwner(BasePermission):
    """Allows read access to any authenticated user, writes only to the owner."""

    def has_object_permission(self, request, view, obj):
        """Compares the profile's user once the object has been loaded."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
