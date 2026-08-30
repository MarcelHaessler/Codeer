from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsCustomerUser(BasePermission):
    """Allows creating reviews only for users with a customer profile."""

    def has_permission(self, request, view):
        """Runs before the view, so there is no object to inspect yet."""
        if request.method in SAFE_METHODS:
            return True
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == 'customer'


class IsReviewAuthor(BasePermission):
    """Allows changing or deleting a review only for its author."""

    def has_object_permission(self, request, view, obj):
        """Compares the author once the review has been loaded."""
        if request.method in SAFE_METHODS:
            return True
        return obj.reviewer == request.user
