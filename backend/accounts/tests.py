from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class AuthenticationTests(APITestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'password': 'testpassword123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        self.user = User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='existingpassword123'
        )

    def test_user_registration(self):
        url = reverse('auth_register')
        response = self.client.post(url, self.user_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.filter(username='testuser').count(), 1)
        self.assertEqual(User.objects.get(username='testuser').email, 'testuser@example.com')

    def test_user_login(self):
        url = reverse('auth_login')
        data = {
            'username': 'existinguser',
            'password': 'existingpassword123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data['user'])
        self.assertIn('refresh', response.data['user'])

    def test_get_user_profile_authenticated(self):
        # Obtain token
        login_url = reverse('auth_login')
        login_data = {
            'username': 'existinguser',
            'password': 'existingpassword123'
        }
        login_response = self.client.post(login_url, login_data, format='json')
        token = login_response.data['user']['token']

        # Get profile
        profile_url = reverse('user_profile')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'existinguser')

    def test_get_user_profile_unauthenticated(self):
        profile_url = reverse('user_profile')
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
