from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

import time

from chats.models import Person, Chat
from projects.models import User, Project

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'adam2@gmail.com'
user_password_2 = 'chips_123'

project_title_1 = "Chat Engine"


class PostChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(
            owner=self.user, title=project_title_1)
        self.person = Person.objects.create(
            project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(
            admin=self.person, project=self.project)

    def test_typing(self):
        time.sleep(1)
        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/typing/'.format(str(self.chat.pk)),
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['id'], self.chat.pk)
        self.assertEqual(data['person'], self.person.username)

    def test_typing_throttle(self):
        time.sleep(1)
        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/typing/'.format(str(self.chat.pk)),
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 200)

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/typing/'.format(str(self.chat.pk)),
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 429)

    def test_cannot_type_without_auth(self):
        time.sleep(1)
        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/typing/'.format(str(self.chat.pk)),
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1
            }
        )

        self.assertEqual(response.status_code, 403)

    def test_cannot_type_in_another_chat(self):
        time.sleep(1)
        temp_person = Person.objects.create(
            project=self.project, username=user_email_2, secret=user_password_2)
        temp_chat = Chat.objects.create(
            admin=temp_person, project=self.project)

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/typing/'.format(str(temp_chat.pk)),
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)
