from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from projects.models import User, Project, Person
from chats.models import Chat

USER = 'adam@gmail.com'
PASSWORD = 'potato_123'

CHAT = 'Chat Test'
PROJECT = "Chat Engine 1"


class InactiveProjectTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.project.is_active = False
        self.project.save()
        self.person = Person.objects.create(username=USER, secret=PASSWORD, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)
        self.client = RequestsClient()

    def test_project_inactive_rejects_public_api(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 403)

        self.project.is_active = True
        self.project.save()
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_project_inactive_rejects_chat_key_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )
        self.assertEqual(response.status_code, 403)

        self.project.is_active = True
        self.project.save()
        response = self.client.get(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )
        self.assertEqual(response.status_code, 200)

    def test_project_inactive_rejects_public_api_with_private_key(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 403)

        self.project.is_active = True
        self.project.save()
        response = self.client.get(
            'http://127.0.0.1:8000/chats/latest/1/',
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 200)

    def test_project_inactive_rejects_private_api(self):
        response = self.client.get(
            'http://127.0.0.1:8000/users/?page=0&page_size=2',
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 403)

        self.project.is_active = True
        self.project.save()
        response = self.client.get(
            'http://127.0.0.1:8000/users/?page=0&page_size=2',
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 200)
