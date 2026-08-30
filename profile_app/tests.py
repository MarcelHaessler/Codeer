from rest_framework import status
from rest_framework.test import APITestCase

from core.test_utils import auth_client, create_user

PROFILE_FIELDS = {
    'user', 'username', 'first_name', 'last_name', 'file', 'location', 'tel',
    'description', 'working_hours', 'type', 'email', 'created_at',
}


class ProfileDetailTests(APITestCase):
    """Covers GET and PATCH on /api/profile/<pk>/."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.client = auth_client(self.business)
        self.url = f'/api/profile/{self.business.id}/'

    def test_is_addressed_by_user_id(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user'], self.business.id)

    def test_returns_all_documented_fields(self):
        response = self.client.get(self.url)
        self.assertEqual(set(response.data), PROFILE_FIELDS)

    def test_requires_authentication(self):
        response = self.client.__class__().get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_writes_name_back_to_user(self):
        data = {'first_name': 'Kevin', 'last_name': 'Mueller'}
        response = self.client.patch(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.business.refresh_from_db()
        self.assertEqual(self.business.first_name, 'Kevin')

    def test_patch_updates_profile_fields(self):
        response = self.client.patch(
            self.url, {'location': 'Berlin'}, format='json'
        )
        self.assertEqual(response.data['location'], 'Berlin')

    def test_patch_rejects_foreign_profile(self):
        url = f'/api/profile/{self.customer.id}/'
        response = self.client.patch(url, {'location': 'X'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_type_cannot_be_changed(self):
        response = self.client.patch(self.url, {'type': 'customer'}, format='json')
        self.assertEqual(response.data['type'], 'business')


class ProfileListTests(APITestCase):
    """Covers the business and customer profile list endpoints."""

    def setUp(self):
        self.business = create_user('kevin', 'business')
        self.customer = create_user('andrey', 'customer')
        self.client = auth_client(self.customer)

    def test_business_list_contains_only_business_profiles(self):
        response = self.client.get('/api/profiles/business/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'business')

    def test_business_list_fields(self):
        response = self.client.get('/api/profiles/business/')
        self.assertEqual(
            set(response.data[0]),
            {
                'user', 'username', 'first_name', 'last_name', 'file',
                'location', 'tel', 'description', 'working_hours', 'type',
            },
        )

    def test_customer_list_uses_uploaded_at(self):
        response = self.client.get('/api/profiles/customer/')
        self.assertEqual(
            set(response.data[0]),
            {
                'user', 'username', 'first_name', 'last_name', 'file',
                'uploaded_at', 'type',
            },
        )

    def test_lists_require_authentication(self):
        response = self.client.__class__().get('/api/profiles/business/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProfileModelTests(APITestCase):
    """Covers the Profile model itself."""

    def test_str_shows_username_and_type(self):
        user = create_user('kevin', 'business')
        self.assertEqual(str(user.profile), 'kevin (business)')
