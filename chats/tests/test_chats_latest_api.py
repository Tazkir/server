from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat
from projects.models import User, Project

from datetime import datetime

EMAIL_1 = 'adam@gmail.com'
PASS_1 = 'potato_123'

EMAIL_2 = 'adam2@gmail.com'
PASS_2 = 'chips_123'

PROJECT = "Chat Engine"
CHAT_1 = "Chat Engine"
CHAT_2 = "Chat Engine 2"


class GetChatsLatestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL_1, password=PASS_1)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=EMAIL_1, secret=PASS_1)
        self.first_chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_1)
        self.second_chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_2)
        self.client = RequestsClient()

    def test_get_chats(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['title'], CHAT_2)

        response = self.client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.first_chat.pk),
            data={"text": 'new msg'},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )

        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['title'], CHAT_1)

        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/3/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['title'], CHAT_1)
        self.assertEqual(data[1]['title'], CHAT_2)

    def test_get_chats_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={}
        )
        self.assertEqual(response.status_code, 403)

    def test_get_chats_needs_to_be_a_chat_person(self):
        Person.objects.create(project=self.project, username=EMAIL_2, secret=PASS_2)

        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_2,
                "user-secret": PASS_2
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)
        self.assertEqual(response.status_code, 200)


class PutChatsLatestTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL_1, password=PASS_1)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=EMAIL_1, secret=PASS_1)
        self.first_chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_1)
        self.second_chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_2)
        self.client = RequestsClient()

    def test_put_chats_before_required(self):
        response = self.client.put(
            'http://127.0.0.1:8000/chats/latest/1/',
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(data['before'], None)

    def test_put_chats_before_must_be_datetime(self):
        response = self.client.put(
            'http://127.0.0.1:8000/chats/latest/1/',
            data={"before": "foo"},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 400)
        self.assertNotEqual(data['before'], None)

    def test_put_chats_latest_first_chat(self):
        response = self.client.put(
            'http://127.0.0.1:8000/chats/latest/1/',
            data={"before": str(datetime.now())},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['title'], CHAT_2)

    def test_put_chats_range_both_chats(self):
        response = self.client.put(
            'http://127.0.0.1:8000/chats/latest/2/',
            data={"before": str(datetime.now())},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['title'], CHAT_2)
        self.assertEqual(data[1]['title'], CHAT_1)

    def test_put_chats_latest_after_first_created(self):
        response = self.client.put(
            'http://127.0.0.1:8000/chats/latest/2/',
            data={"before": str(self.second_chat.created)},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['title'], CHAT_1)

    def test_put_chats_latest_zero_list(self):
        response = self.client.put(
            'http://127.0.0.1:8000/chats/latest/0/',
            data={"before": str(datetime.now())},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)
        self.assertEqual(response.status_code, 200)

    def test_put_chats_latest_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={}
        )
        self.assertEqual(response.status_code, 403)

    def test_put_chats_latest_needs_to_be_a_chat_person(self):
        Person.objects.create(project=self.project, username=EMAIL_2, secret=PASS_2)
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_2,
                "user-secret": PASS_2
            }
        )
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)
        self.assertEqual(response.status_code, 200)
