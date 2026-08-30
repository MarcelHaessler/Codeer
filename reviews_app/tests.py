from rest_framework import status
from rest_framework.test import APITestCase

from core.test_utils import auth_client, create_user
from reviews_app.models import Review

REVIEWS_URL = '/api/reviews/'


class ReviewCreateTests(APITestCase):
    """Covers POST /api/reviews/ and its validation rules."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.client = auth_client(self.customer)

    def payload(self, **overrides):
        """Returns a valid review body with optional overrides."""
        data = {
            'business_user': self.business.id,
            'rating': 4,
            'description': 'Sehr professionell.',
        }
        data.update(overrides)
        return data

    def test_creates_review_with_request_user_as_reviewer(self):
        response = self.client.post(REVIEWS_URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['reviewer'], self.customer.id)

    def test_rejects_second_review_for_same_business(self):
        self.client.post(REVIEWS_URL, self.payload(), format='json')
        response = self.client.post(REVIEWS_URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_allows_review_for_another_business(self):
        other = create_user('sarah', 'business')
        self.client.post(REVIEWS_URL, self.payload(), format='json')
        response = self.client.post(
            REVIEWS_URL, self.payload(business_user=other.id), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_rejects_business_user_as_author(self):
        client = auth_client(self.business)
        response = client.post(REVIEWS_URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_review_about_a_customer(self):
        data = self.payload(business_user=self.customer.id)
        response = self.client.post(REVIEWS_URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_rating_above_five(self):
        response = self.client.post(
            REVIEWS_URL, self.payload(rating=9), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_rating_below_one(self):
        response = self.client.post(
            REVIEWS_URL, self.payload(rating=0), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ReviewAccessTests(APITestCase):
    """Covers listing, filtering, updating and deleting reviews."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.other = create_user('sarah', 'customer')
        self.review = Review.objects.create(
            business_user=self.business, reviewer=self.customer,
            rating=4, description='Gut',
        )
        self.client = auth_client(self.customer)
        self.url = f'{REVIEWS_URL}{self.review.id}/'

    def test_filters_by_business_user(self):
        url = f'{REVIEWS_URL}?business_user_id={self.business.id}'
        self.assertEqual(len(self.client.get(url).data), 1)

    def test_filters_by_reviewer(self):
        url = f'{REVIEWS_URL}?reviewer_id={self.other.id}'
        self.assertEqual(len(self.client.get(url).data), 0)

    def test_accepts_descending_ordering(self):
        response = self.client.get(f'{REVIEWS_URL}?ordering=-updated_at')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_author_can_update(self):
        response = self.client.patch(self.url, {'rating': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['rating'], 5)

    def test_business_user_cannot_be_changed(self):
        data = {'business_user': self.other.id}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.data['business_user'], self.business.id)

    def test_other_user_cannot_update(self):
        client = auth_client(self.other)
        response = client.patch(self.url, {'rating': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_author_can_delete(self):
        self.assertEqual(
            self.client.delete(self.url).status_code, status.HTTP_204_NO_CONTENT
        )

    def test_other_user_cannot_delete(self):
        client = auth_client(self.other)
        self.assertEqual(
            client.delete(self.url).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_any_authenticated_user_can_read_single_review(self):
        client = auth_client(self.other)
        response = client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_str_shows_reviewer_and_business_user(self):
        self.assertEqual(str(self.review), 'andrey -> kevin')
