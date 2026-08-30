from django.db.models import Avg, Count
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from offers_app.models import Offer
from profile_app.models import Profile
from reviews_app.models import Review


class BaseInfoView(APIView):
    """Returns aggregated statistics about the whole platform."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Falls back to 0 for the average while no review exists yet."""
        stats = Review.objects.aggregate(total=Count('id'), average=Avg('rating'))
        return Response(
            {
                'review_count': stats['total'],
                'average_rating': round(stats['average'], 1) if stats['average'] else 0,
                'business_profile_count': Profile.objects.filter(
                    type='business'
                ).count(),
                'offer_count': Offer.objects.count(),
            },
            status=status.HTTP_200_OK,
        )
