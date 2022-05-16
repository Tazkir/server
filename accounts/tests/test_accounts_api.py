import pytz
from datetime import datetime, timedelta

from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory

from accounts.models import User, Reset
from accounts.views import Accounts

user_email_1 = 'alamorre@gmail.com'
user_email_2 = 'Alamorre@gmail.COM'
user_password_1 = 'potato_123'

different_email = 'adam@mail.co'


class PostAccountsTestCase(APITestCase):

    def test_register(self):
        factory = APIRequestFactory()
        view = Accounts.as_view()

        request = factory.post(
            '/accounts/',
            json.dumps({"email": user_email_1, "password": user_password_1}),
            content_type='application/json'
        )
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertNotEqual(response.data['token'], None)
        self.assertEqual(response.data['user']['email'], user_email_1)
        self.assertEqual(len(User.objects.all()), 1)

    def test_cannot_register_email_again_different_cases(self):
        factory = APIRequestFactory()
        view = Accounts.as_view()

        request = factory.post(
            '/accounts/',
            json.dumps({"email": user_email_1, "password": user_password_1}),
            content_type='application/json'
        )
        response_1 = view(request)

        request = factory.post(
            '/accounts/',
            json.dumps({"email": user_email_2, "password": user_password_1}),
            content_type='application/json'
        )
        response_2 = view(request)

        self.assertEqual(response_1.status_code, 201)
        self.assertEqual(response_2.status_code, 400)
        self.assertEqual(len(User.objects.all()), 1)

    def test_register_bad_email(self):
        factory = APIRequestFactory()
        view = Accounts.as_view()

        request = factory.post(
            '/accounts/',
            json.dumps({"email": None, "password": user_password_1}),
            content_type='application/json'
        )
        response = view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(User.objects.all()), 0)

    def test_register_bad_password(self):
        factory = APIRequestFactory()
        view = Accounts.as_view()

        request = factory.post(
            '/accounts/',
            json.dumps({"email": user_email_1, "password": None}),
            content_type='application/json'
        )
        response = view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(User.objects.all()), 0)


class PutAccountsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email=user_email_1, password=user_password_1)

    def test_forgot_password_valid_email_plus_refresh(self):
        factory = APIRequestFactory()
        view = Accounts.as_view()

        request = factory.put('/accounts/', json.dumps({"email": user_email_1}), content_type='application/json')
        response = view(request)
        reset_1 = Reset.objects.first()

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(reset_1.uuid, None)
        self.assertGreater(reset_1.expiry, datetime.now().replace(tzinfo=pytz.UTC))

        request = factory.put('/accounts/', json.dumps({"email": user_email_1}), content_type='application/json')
        response = view(request)
        reset_2 = Reset.objects.first()

        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(reset_2.uuid, reset_1.uuid)
        self.assertGreater(reset_2.expiry, reset_1.expiry)

    def test_forgot_password_no_user(self):
        factory = APIRequestFactory()
        view = Accounts.as_view()

        request = factory.put('/accounts/', json.dumps({"email": different_email}), content_type='application/json')
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Reset.objects.all()), 0)

    def test_forgot_password_invalid_email(self):
        factory = APIRequestFactory()
        view = Accounts.as_view()

        request = factory.put('/accounts/', json.dumps({"email": '...'}), content_type='application/json')
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Reset.objects.all()), 0)
