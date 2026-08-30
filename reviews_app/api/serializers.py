from rest_framework import serializers

from ..models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Creates and lists reviews; the reviewer is taken from the request."""

    class Meta:
        model = Review
        fields = [
            'id', 'business_user', 'reviewer', 'rating', 'description',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'reviewer', 'created_at', 'updated_at']

    def validate_business_user(self, value):
        """Keeps ratings off customers and off users without a profile."""
        profile = getattr(value, 'profile', None)
        if profile is None or profile.type != 'business':
            raise serializers.ValidationError('This user is not a business user.')
        return value

    def validate(self, attrs):
        """Checks for a duplicate on create only, so edits stay possible."""
        if self.instance is None:
            self._reject_duplicate(attrs.get('business_user'))
        return attrs

    def _reject_duplicate(self, business_user):
        """Allows only one review per reviewer and business user."""
        reviewer = self.context['request'].user
        exists = Review.objects.filter(
            business_user=business_user, reviewer=reviewer
        ).exists()
        if exists:
            raise serializers.ValidationError(
                {'detail': 'You have already reviewed this business user.'}
            )


class ReviewUpdateSerializer(ReviewSerializer):
    """Limits updates to the rating and the description."""

    class Meta(ReviewSerializer.Meta):
        read_only_fields = [
            'id', 'business_user', 'reviewer', 'created_at', 'updated_at',
        ]
