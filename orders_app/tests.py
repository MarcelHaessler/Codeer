from rest_framework import status
from rest_framework.test import APITestCase

from core.test_utils import auth_client, create_offer, create_user
from orders_app.models import Order

ORDERS_URL = '/api/orders/'


class OrderCreateTests(APITestCase):
    """Covers POST /api/orders/ and the snapshot behaviour."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.offer = create_offer(self.business)
        self.detail = self.offer.details.get(offer_type='standard')
        self.client = auth_client(self.customer)

    def test_creates_order_from_offer_detail(self):
        data = {'offer_detail_id': self.detail.id}
        response = self.client.post(ORDERS_URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['business_user'], self.business.id)
        self.assertEqual(response.data['customer_user'], self.customer.id)

    def test_starts_in_progress(self):
        data = {'offer_detail_id': self.detail.id}
        response = self.client.post(ORDERS_URL, data, format='json')
        self.assertEqual(response.data['status'], 'in_progress')

    def test_copies_tier_data(self):
        data = {'offer_detail_id': self.detail.id}
        response = self.client.post(ORDERS_URL, data, format='json')
        self.assertEqual(response.data['price'], 200)
        self.assertEqual(response.data['offer_type'], 'standard')

    def test_order_is_unaffected_by_later_offer_changes(self):
        data = {'offer_detail_id': self.detail.id}
        order_id = self.client.post(ORDERS_URL, data, format='json').data['id']
        self.detail.price = 999
        self.detail.title = 'Changed'
        self.detail.save()
        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.price, 200)
        self.assertNotEqual(order.title, 'Changed')

    def test_rejects_business_user(self):
        client = auth_client(self.business)
        data = {'offer_detail_id': self.detail.id}
        response = client.post(ORDERS_URL, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_missing_offer_detail_id(self):
        response = self.client.post(ORDERS_URL, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('offer_detail_id', response.data)

    def test_rejects_non_numeric_offer_detail_id(self):
        response = self.client.post(
            ORDERS_URL, {'offer_detail_id': 'sdfg'}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('offer_detail_id', response.data)

    def test_rejects_zero_or_negative_offer_detail_id(self):
        for value in (0, -1):
            response = self.client.post(
                ORDERS_URL, {'offer_detail_id': value}, format='json'
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_404_for_unknown_offer_detail(self):
        response = self.client.post(
            ORDERS_URL, {'offer_detail_id': 9999}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderAccessTests(APITestCase):
    """Covers listing, status updates and deletion of orders."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.outsider = create_user('sarah', 'customer')
        offer = create_offer(self.business)
        detail = offer.details.get(offer_type='basic')
        client = auth_client(self.customer)
        self.order_id = client.post(
            ORDERS_URL, {'offer_detail_id': detail.id}, format='json'
        ).data['id']
        self.url = f'{ORDERS_URL}{self.order_id}/'

    def test_both_parties_see_the_order(self):
        for user in (self.customer, self.business):
            response = auth_client(user).get(ORDERS_URL)
            self.assertEqual(len(response.data), 1)

    def test_uninvolved_user_sees_nothing(self):
        response = auth_client(self.outsider).get(ORDERS_URL)
        self.assertEqual(len(response.data), 0)

    def test_business_user_updates_status(self):
        client = auth_client(self.business)
        response = client.patch(self.url, {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'completed')

    def test_customer_cannot_update_status(self):
        client = auth_client(self.customer)
        response = client.patch(self.url, {'status': 'completed'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_rejects_invalid_status(self):
        client = auth_client(self.business)
        response = client.patch(self.url, {'status': 'nonsense'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_price_cannot_be_changed(self):
        client = auth_client(self.business)
        response = client.patch(self.url, {'price': 1}, format='json')
        self.assertEqual(response.data['price'], 100)

    def test_delete_requires_staff(self):
        client = auth_client(self.business)
        self.assertEqual(
            client.delete(self.url).status_code, status.HTTP_403_FORBIDDEN
        )

    def test_staff_can_delete(self):
        self.business.is_staff = True
        self.business.save()
        client = auth_client(self.business)
        self.assertEqual(
            client.delete(self.url).status_code, status.HTTP_204_NO_CONTENT
        )


class OrderCountTests(APITestCase):
    """Covers the in-progress and completed order count endpoints."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        offer = create_offer(self.business)
        self.client = auth_client(self.customer)
        self.client.post(
            ORDERS_URL,
            {'offer_detail_id': offer.details.first().id},
            format='json',
        )

    def test_counts_orders_in_progress(self):
        response = self.client.get(f'/api/order-count/{self.business.id}/')
        self.assertEqual(response.data, {'order_count': 1})

    def test_counts_completed_orders(self):
        url = f'/api/completed-order-count/{self.business.id}/'
        self.assertEqual(self.client.get(url).data, {'completed_order_count': 0})
        Order.objects.update(status='completed')
        self.assertEqual(self.client.get(url).data, {'completed_order_count': 1})

    def test_returns_404_for_unknown_user(self):
        response = self.client.get('/api/order-count/9999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class OrderModelTests(APITestCase):
    """Covers reading a single order and the Order model itself."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        offer = create_offer(self.business)
        detail = offer.details.get(offer_type='basic')
        self.client = auth_client(self.customer)
        self.order_id = self.client.post(
            ORDERS_URL, {'offer_detail_id': detail.id}, format='json'
        ).data['id']

    def test_involved_user_can_read_single_order(self):
        response = self.client.get(f'{ORDERS_URL}{self.order_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_str_shows_title_and_status(self):
        order = Order.objects.get(pk=self.order_id)
        self.assertEqual(str(order), f'{order.title} (in_progress)')
