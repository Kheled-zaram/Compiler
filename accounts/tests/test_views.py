from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from accounts.views import LoginView, LogoutView


class LogInTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'testuser',
            'password': 'secret'}
        User.objects.create_user(**self.credentials)
        self.url = reverse('accounts:login')

    def test_login(self):
        response = self.client.post(self.url, self.credentials, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_active)

    def test_incorrect_password(self):
        self.credentials['password'] = 'wrong_password'
        response = self.client.post(self.url, self.credentials, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_active)

    def test_user_does_not_exist(self):
        self.credentials['username'] = 'not_exists'
        response = self.client.post(self.url, self.credentials, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_active)


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.url = reverse('accounts:logout')

    def test_logout_view(self):

        self.client.force_login(self.user)
        self.assertTrue(self.user.is_authenticated)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))

        self.assertFalse(response.wsgi_request.user.is_authenticated)
