from rest_framework import serializers

from ..models import Profile


class BaseProfileSerializer(serializers.ModelSerializer):
    """Shares the read-only fields that are derived from the related User."""

    user = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)


class ProfileSerializer(BaseProfileSerializer):
    """Full profile representation used for retrieve and update."""

    first_name = serializers.CharField(
        source='user.first_name', required=False, allow_blank=True
    )
    last_name = serializers.CharField(
        source='user.last_name', required=False, allow_blank=True
    )
    email = serializers.EmailField(source='user.email', required=False)

    class Meta:
        model = Profile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file', 'location',
            'tel', 'description', 'working_hours', 'type', 'email', 'created_at',
        ]
        read_only_fields = ['type', 'created_at']

    def update(self, instance, validated_data):
        """Name and email live on the user, so they are written back there."""
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(instance.user, attr, value)
        if user_data:
            instance.user.save()
        return super().update(instance, validated_data)


class BusinessProfileListSerializer(BaseProfileSerializer):
    """Reduced representation for the business profile list."""

    class Meta:
        model = Profile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file', 'location',
            'tel', 'description', 'working_hours', 'type',
        ]


class CustomerProfileListSerializer(BaseProfileSerializer):
    """Reduced representation for the customer profile list."""

    uploaded_at = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'user', 'username', 'first_name', 'last_name', 'file',
            'uploaded_at', 'type',
        ]
