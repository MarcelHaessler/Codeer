from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from core.test_utils import auth_client, create_offer, create_user, tier_payload

OFFERS_URL = '/api/offers/'


class OfferCreateTests(APITestCase):
    """Covers POST /api/offers/."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.client = auth_client(self.business)

    def payload(self, tiers=('basic', 'standard', 'premium')):
        """Returns an offer body with one detail per given tier."""
        return {
            'title': 'Grafikdesign-Paket',
            'description': 'Ein umfassendes Paket.',
            'details': [tier_payload(tier) for tier in tiers],
        }

    def test_creates_offer_with_three_details(self):
        response = self.client.post(OFFERS_URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['details']), 3)

    def test_assigns_offer_to_requesting_user(self):
        self.client.post(OFFERS_URL, self.payload(), format='json')
        self.assertEqual(self.business.offers.count(), 1)

    def test_rejects_customer_user(self):
        client = auth_client(self.customer)
        response = client.post(OFFERS_URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_anonymous_user(self):
        response = APIClient().post(OFFERS_URL, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_rejects_incomplete_tiers(self):
        response = self.client.post(
            OFFERS_URL, self.payload(tiers=('basic',)), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_duplicate_tiers(self):
        response = self.client.post(
            OFFERS_URL, self.payload(tiers=('basic', 'basic', 'premium')),
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_negative_delivery_time(self):
        data = self.payload()
        data['details'][0]['delivery_time_in_days'] = -1
        response = self.client.post(OFFERS_URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class OfferListTests(APITestCase):
    """Covers GET /api/offers/ including filtering and ordering."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.other = create_user('sarah', 'business')
        self.offer = create_offer(self.business, title='Webdesign')
        create_offer(self.other, title='Logo')
        self.client = auth_client(create_user('andrey', 'customer'))

    def test_returns_paginated_results(self):
        response = self.client.get(OFFERS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_is_public(self):
        """The API docs list no permissions for the offer list endpoint."""
        response = APIClient().get(OFFERS_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_filters_work_without_a_token(self):
        url = f'{OFFERS_URL}?creator_id={self.other.id}&ordering=min_price'
        response = APIClient().get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_includes_aggregates_and_creator(self):
        response = self.client.get(OFFERS_URL)
        first = response.data['results'][0]
        self.assertEqual(first['min_price'], 100)
        self.assertEqual(first['min_delivery_time'], 5)
        self.assertIn('username', first['user_details'])

    def test_details_are_reduced_to_id_and_url(self):
        response = self.client.get(OFFERS_URL)
        detail = response.data['results'][0]['details'][0]
        self.assertEqual(set(detail), {'id', 'url'})

    def test_filters_by_creator(self):
        response = self.client.get(f'{OFFERS_URL}?creator_id={self.other.id}')
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], 'Logo')

    def test_filters_by_min_price(self):
        response = self.client.get(f'{OFFERS_URL}?min_price=200')
        self.assertEqual(response.data['count'], 0)

    def test_filters_by_max_delivery_time(self):
        response = self.client.get(f'{OFFERS_URL}?max_delivery_time=5')
        self.assertEqual(response.data['count'], 2)

    def test_searches_title(self):
        response = self.client.get(f'{OFFERS_URL}?search=Logo')
        self.assertEqual(response.data['count'], 1)

    def test_respects_page_size(self):
        response = self.client.get(f'{OFFERS_URL}?page_size=1')
        self.assertEqual(len(response.data['results']), 1)


class OfferDetailTests(APITestCase):
    """Covers retrieve, update and delete of a single offer."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.offer = create_offer(self.business)
        self.client = auth_client(self.business)
        self.url = f'{OFFERS_URL}{self.offer.id}/'

    def test_retrieve_omits_user_details(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('user_details', response.data)

    def test_patch_updates_matching_tier(self):
        data = {'details': [tier_payload('basic', price=120)]}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        prices = {d['offer_type']: d['price'] for d in response.data['details']}
        self.assertEqual(prices['basic'], 120)
        self.assertEqual(prices['standard'], 200)

    def test_patch_rejects_non_owner(self):
        client = auth_client(self.customer)
        response = client.patch(self.url, {'title': 'Hack'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_by_owner(self):
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_rejects_non_owner(self):
        client = auth_client(self.customer)
        self.assertEqual(
            client.delete(self.url).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_offerdetail_endpoint_returns_full_tier(self):
        detail = self.offer.details.first()
        response = self.client.get(f'/api/offerdetails/{detail.id}/')
        self.assertEqual(
            set(response.data),
            {
                'id', 'title', 'revisions', 'delivery_time_in_days', 'price',
                'features', 'offer_type',
            },
        )


class OfferPatchValidationTests(APITestCase):
    """Covers the validation rules for the details sent with PATCH."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.offer = create_offer(self.business)
        self.client = auth_client(self.business)
        self.url = f'{OFFERS_URL}{self.offer.id}/'

    def patch_details(self, *details):
        """Sends the given detail entries and returns the response."""
        return self.client.patch(self.url, {'details': list(details)}, format='json')

    def test_requires_offer_type_in_each_detail(self):
        response = self.patch_details({'title': 'No type given'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('details', response.data)

    def test_rejects_empty_detail(self):
        response = self.patch_details({})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_duplicate_offer_type(self):
        response = self.patch_details(
            {'offer_type': 'basic', 'price': 1}, {'offer_type': 'basic', 'price': 2}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_negative_delivery_time(self):
        response = self.patch_details({'offer_type': 'basic', 'delivery_time_in_days': -3})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_negative_price(self):
        response = self.patch_details({'offer_type': 'basic', 'price': -10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_revisions_below_minus_one(self):
        response = self.patch_details({'offer_type': 'basic', 'revisions': -5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_allows_unlimited_revisions(self):
        response = self.patch_details({'offer_type': 'basic', 'revisions': -1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rejects_features_that_are_not_a_list(self):
        response = self.patch_details({'offer_type': 'basic', 'features': 'nope'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_leaves_other_tiers_untouched(self):
        self.patch_details({'offer_type': 'premium', 'price': 999})
        prices = {d.offer_type: d.price for d in self.offer.details.all()}
        self.assertEqual(prices['basic'], 100)
        self.assertEqual(prices['premium'], 999)


class OfferModelTests(APITestCase):
    """Covers the Offer and OfferDetail models themselves."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.offer = create_offer(self.business, title='Webdesign')

    def test_offer_str_is_title(self):
        self.assertEqual(str(self.offer), 'Webdesign')

    def test_detail_str_shows_offer_and_type(self):
        detail = self.offer.details.get(offer_type='basic')
        self.assertEqual(str(detail), 'Webdesign - basic')
