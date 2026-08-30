from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from core.test_utils import TEST_PASSWORD, create_user


class RegistrationTests(APITestCase):
    """Covers POST /api/registration/."""

    url = '/api/registration/'

    def payload(self, **overrides):
        """Returns a valid registration body with optional overrides."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'secret123',
            'repeated_password': 'secret123',
            'type': 'customer',
        }
        data.update(overrides)
        return data

    def test_creates_user_and_returns_token(self):
        response = self.client.post(self.url, self.payload(), format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            set(response.data), {'token', 'username', 'email', 'user_id'}
        )

    def test_creates_profile_with_given_type(self):
        self.client.post(self.url, self.payload(type='business'), format='json')
        user = User.objects.get(username='newuser')
        self.assertEqual(user.profile.type, 'business')

    def test_stores_password_hashed(self):
        self.client.post(self.url, self.payload(), format='json')
        user = User.objects.get(username='newuser')
        self.assertTrue(user.check_password('secret123'))
        self.assertNotEqual(user.password, 'secret123')

    def test_rejects_password_mismatch(self):
        data = self.payload(repeated_password='different')
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('repeated_password', response.data)

    def test_rejects_missing_email(self):
        data = self.payload()
        del data['email']
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_rejects_duplicate_email(self):
        self.client.post(self.url, self.payload(), format='json')
        response = self.client.post(
            self.url, self.payload(username='other'), format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class LoginTests(APITestCase):
    """Covers POST /api/login/."""

    url = '/api/login/'

    def setUp(self):
        self.user = create_user('kevin', 'business')

    def test_returns_token_for_valid_credentials(self):
        data = {'username': 'kevin', 'password': TEST_PASSWORD}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.id)
        self.assertTrue(response.data['token'])

    def test_rejects_wrong_password(self):
        data = {'username': 'kevin', 'password': 'wrong'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rejects_unknown_user(self):
        data = {'username': 'ghost', 'password': TEST_PASSWORD}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
