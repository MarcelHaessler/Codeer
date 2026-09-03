from rest_framework import serializers

from ..models import Offer, OfferDetail

DETAIL_FIELDS = [
    'id', 'title', 'revisions', 'delivery_time_in_days', 'price', 'features',
    'offer_type',
]


class OfferDetailSerializer(serializers.ModelSerializer):
    """Full representation of a single pricing tier.

    The numeric limits are declared here because writes to existing tiers
    bypass model validation and would otherwise fail inside the database.
    """

    price = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    delivery_time_in_days = serializers.IntegerField(min_value=0)
    features = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = OfferDetail
        fields = DETAIL_FIELDS

    def validate_revisions(self, value):
        """Allows -1 for unlimited revisions, but no other negative number."""
        if value < -1:
            raise serializers.ValidationError(
                'Use -1 for unlimited revisions or a number of 0 or more.'
            )
        return value


class OfferDetailLinkSerializer(serializers.ModelSerializer):
    """Reference form of a tier, used inside offer list and retrieve responses."""

    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj):
        """Points at the tier's own endpoint; the frontend only reads the id."""
        return f'/api/offerdetails/{obj.id}/'


class OfferListSerializer(serializers.ModelSerializer):
    """Offer representation for the list endpoint, including its creator."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time',
            'user_details',
        ]

    def get_min_price(self, obj):
        """Reads the value annotated by the queryset, not a model field."""
        return obj.min_price

    def get_min_delivery_time(self, obj):
        """Reads the value annotated by the queryset, not a model field."""
        return obj.min_delivery_time

    def get_user_details(self, obj):
        """Flattens the creator's name fields into the offer response."""
        return {
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'username': obj.user.username,
        }


class OfferRetrieveSerializer(serializers.ModelSerializer):
    """Offer representation for the detail endpoint, without creator data."""

    details = OfferDetailLinkSerializer(many=True, read_only=True)
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()

    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time',
        ]

    def get_min_price(self, obj):
        """Reads the value annotated by the queryset, not a model field."""
        return obj.min_price

    def get_min_delivery_time(self, obj):
        """Reads the value annotated by the queryset, not a model field."""
        return obj.min_delivery_time


class OfferWriteSerializer(serializers.ModelSerializer):
    """Creates and updates an offer together with its nested tiers."""

    details = OfferDetailSerializer(many=True)

    class Meta:
        model = Offer
        fields = ['id', 'title', 'image', 'description', 'details']

    def validate_details(self, value):
        """Every tier must name its offer_type; a new offer needs all three."""
        types = [item.get('offer_type') for item in value]
        if None in types:
            raise serializers.ValidationError('Each detail must include its offer_type.')
        if len(types) != len(set(types)):
            raise serializers.ValidationError('Each offer_type may appear only once.')
        if self.instance is None:
            self._validate_complete_tiers(types)
        return value

    def _validate_complete_tiers(self, types):
        """Requires exactly one basic, standard and premium tier on create."""
        if sorted(types) != ['basic', 'premium', 'standard']:
            raise serializers.ValidationError(
                'Exactly one basic, standard and premium detail is required.'
            )

    def create(self, validated_data):
        """Saves the offer first, because the tiers need its id as a foreign key."""
        details_data = validated_data.pop('details')
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        """Leaves the tiers untouched when the request omits them entirely."""
        details_data = validated_data.pop('details', None)
        instance = super().update(instance, validated_data)
        if details_data is not None:
            self._update_details(instance, details_data)
        return instance

    def _update_details(self, offer, details_data):
        """Updates existing tiers in place, matched by their offer_type."""
        for detail_data in details_data:
            offer.details.filter(offer_type=detail_data['offer_type']).update(**detail_data)
