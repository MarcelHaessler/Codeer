from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsCustomerUser(BasePermission):
    """Allows creating orders only for users with a customer profile."""

    def has_permission(self, request, view):
        """Runs before the view, so there is no object to inspect yet."""
        if request.method in SAFE_METHODS:
            return True
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == 'customer'


class IsOrderBusinessUserOrAdmin(BasePermission):
    """Limits status updates to the assigned business user, deletion to staff."""

    def has_permission(self, request, view):
        """Stops non-staff deletions early, before the order is even loaded."""
        if request.method == 'DELETE':
            return request.user.is_staff
        return True

    def has_object_permission(self, request, view, obj):
        """Compares the order's business user once the object exists."""
        if request.method == 'DELETE':
            return request.user.is_staff
        if request.method == 'PATCH':
            return obj.business_user == request.user
        return True
