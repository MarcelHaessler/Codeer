from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsBusinessUser(BasePermission):
    """Allows write access only to users with a business profile."""

    def has_permission(self, request, view):
        """Runs before the view, so there is no object to inspect yet."""
        if request.method in SAFE_METHODS:
            return True
        profile = getattr(request.user, 'profile', None)
        return profile is not None and profile.type == 'business'


class IsOfferOwner(BasePermission):
    """Allows changes to an offer only for the user who created it."""

    def has_object_permission(self, request, view, obj):
        """Compares the creator once the offer has been loaded."""
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user
