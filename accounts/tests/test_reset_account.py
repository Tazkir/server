from datetime import datetime, timedelta

import time
import uuid
import pytz

from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory

from accounts.models import User, Reset
from accounts.views import ResetAccount

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'


class GetAccountTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.token = Token.objects.create(user=self.user)
        self.reset = Reset.objects.create(user=self.user)

    def test_get_your_account_then_deleted(self):
        factory = APIRequestFactory()
        view = ResetAccount.as_view()
        request = factory.get('/accounts/{}/'.format(str(self.reset.uuid)))

        response = view(request, reset_uuid=str(self.reset.uuid))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Reset.objects.all()), 0)
        self.assertEqual(response.data['user']['email'], user_email_1)
        self.assertEqual(response.data['token'], self.token.key)

        factory = APIRequestFactory()
        view = ResetAccount.as_view()
        request = factory.get('/accounts/{}/'.format(str(self.reset.uuid)))

        response = view(request, reset_uuid=str(self.reset.uuid))
        self.assertEqual(response.status_code, 404)

    def test_get_your_account_expired_reset(self):
        now = datetime.now().replace(tzinfo=pytz.UTC)
        self.reset.expiry = now + timedelta(seconds=1)
        self.reset.save()

        time.sleep(2)

        factory = APIRequestFactory()
        view = ResetAccount.as_view()
        request = factory.get('/accounts/{}/'.format(str(self.reset.uuid)))

        response = view(request, reset_uuid=str(self.reset.uuid))
        self.assertEqual(response.status_code, 404)

    def test_get_your_account_different_uuid(self):
        factory = APIRequestFactory()
        view = ResetAccount.as_view()

        new_uuid = str(uuid.uuid4())
        request = factory.get('/accounts/{}/'.format(new_uuid))

        response = view(request, reset_uuid=new_uuid)
        self.assertEqual(response.status_code, 404)

    def test_get_your_account_invalid_uuid(self):
        factory = APIRequestFactory()
        view = ResetAccount.as_view()

        bad_uuid = '123-123-123-123-123'
        request = factory.get('/accounts/{}/'.format(bad_uuid))

        response = view(request, reset_uuid=bad_uuid)
        self.assertEqual(response.status_code, 404)
