from rest_framework import status
from rest_framework.test import APITestCase

from core.test_utils import create_offer, create_user
from reviews_app.models import Review

BASE_INFO_URL = '/api/base-info/'


class BaseInfoTests(APITestCase):
    """Covers GET /api/base-info/."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        create_offer(self.business)

    def test_is_public(self):
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_returns_all_documented_fields(self):
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(
            set(response.data),
            {
                'review_count', 'average_rating', 'business_profile_count',
                'offer_count',
            },
        )

    def test_counts_offers_and_business_profiles(self):
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(response.data['offer_count'], 1)
        self.assertEqual(response.data['business_profile_count'], 1)

    def test_average_rating_is_rounded(self):
        Review.objects.create(
            business_user=self.business, reviewer=self.customer,
            rating=4, description='Gut',
        )
        other = create_user('sarah', 'customer')
        Review.objects.create(
            business_user=self.business, reviewer=other,
            rating=5, description='Top',
        )
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(response.data['average_rating'], 4.5)

    def test_handles_empty_database(self):
        response = self.client.get(BASE_INFO_URL)
        self.assertEqual(response.data['review_count'], 0)
        self.assertEqual(response.data['average_rating'], 0)
