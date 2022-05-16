from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from accounts.models import User
from accounts.views import MyDetails

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'eve@gmail.com'
user_password_2 = 'guacamole_123'


class GetAccountTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=user_email_1, password=user_password_1)

    def test_get_your_account(self):
        factory = APIRequestFactory()
        view = MyDetails.as_view()
        request = factory.get('/accounts/me/')
        force_authenticate(request, user=self.user)

        response = view(request)
        self.assertEqual(response.status_code, 200)

    def test_get_your_account_needs_auth(self):
        factory = APIRequestFactory()
        view = MyDetails.as_view()
        request = factory.get('/accounts/')

        response = view(request)
        self.assertEqual(response.status_code, 401)


class PatchAccountTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=user_email_1, password=user_password_1)

    def test_edit_your_account(self):
        factory = APIRequestFactory()
        view = MyDetails.as_view()

        request = factory.patch(
            '/accounts/me/',
            json.dumps({"email": user_email_1, "password": user_password_1}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response_1 = view(request)

        password_1 = User.objects.get(email=user_email_1).password

        request = factory.patch(
            '/accounts/me/',
            json.dumps({"email": user_email_2, "password": user_password_2}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response_2 = view(request)

        password_2 = User.objects.get(email=user_email_2).password

        self.assertEqual(response_1.status_code, 200)
        self.assertEqual(response_2.status_code, 200)

        self.assertNotEqual(password_1, password_2)
        self.assertNotEqual(response_1.data['email'], response_2.data['email'])

    def test_edit_your_account_needs_auth(self):
        factory = APIRequestFactory()
        view = MyDetails.as_view()
        request = factory.patch(
            '/accounts/me/',
            json.dumps({"email": user_email_1, "password": user_password_1}),
            content_type='application/json'
        )
        response = view(request)

        self.assertEqual(response.status_code, 401)

    def test_delete_your_account(self):
        factory = APIRequestFactory()
        view = MyDetails.as_view()
        request = factory.delete(
            '/accounts/me/', content_type='application/json')
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 200)

        users = User.objects.all()
        self.assertEqual(len(users), 0)

    def test_delete_your_account_needs_auth(self):
        factory = APIRequestFactory()
        view = MyDetails.as_view()
        request = factory.delete(
            '/accounts/me/', content_type='application/json')
        response = view(request)

        self.assertEqual(response.status_code, 401)

        users = User.objects.all()
        self.assertEqual(len(users), 1)
