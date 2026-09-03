from rest_framework import serializers

from ..models import Order


class OrderCreateSerializer(serializers.Serializer):
    """Validates the single input needed to book an offer tier.

    The tier id arrives as a plain number, so a non-numeric value has to be
    rejected here instead of failing inside the database lookup.
    """

    offer_detail_id = serializers.IntegerField(min_value=1)


class OrderSerializer(serializers.ModelSerializer):
    """Represents an order; only the status may be changed after creation."""

    class Meta:
        model = Order
        fields = [
            'id', 'customer_user', 'business_user', 'title', 'revisions',
            'delivery_time_in_days', 'price', 'features', 'offer_type',
            'status', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'customer_user', 'business_user', 'title', 'revisions',
            'delivery_time_in_days', 'price', 'features', 'offer_type',
            'created_at', 'updated_at',
        ]
