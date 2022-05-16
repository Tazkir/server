from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat
from projects.models import User, Project

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'eve@gmail.com'
user_password_2 = 'pretzel_123'

project_title_1 = "Chat Engine Project 1"
project_title_2 = "Chat Engine Project 2"

chat_title_1 = "Chat Engine Chat 1"
chat_title_2 = "Chat Engine Chat 2"


class GetChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)

    def test_get_chat(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "project-id": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['admin']['username'], user_email_1)
        self.assertEqual(data['title'], chat_title_1)
        self.assertTrue(len(data['access_key']) > 0)

    def test_get_chat_with_chat_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "project-id": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['admin']['username'], user_email_1)
        self.assertEqual(data['title'], chat_title_1)
        self.assertTrue(len(data['access_key']) > 0)

    def test_get_chat_needs_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "project-id": str(self.project.public_key),
                "user-name": '...',
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 403)


class PatchChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)

    def test_patch_chat(self):
        self.assertEqual(self.chat.is_direct_chat, False)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            data={"title": chat_title_2, 'is_direct_chat': True},
            headers={
                "project-id": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['title'], chat_title_2)
        self.assertEqual(data['is_direct_chat'], True)
        self.assertEqual(Chat.objects.first().title, chat_title_2)
        self.assertEqual(Chat.objects.first().is_direct_chat, True)

    def test_patch_chat_with_chat_auth(self):
        self.assertEqual(self.chat.is_direct_chat, False)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            data={"title": chat_title_2, 'is_direct_chat': True},
            headers={
                "project-id": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)

        self.assertEqual(data['title'], chat_title_2)
        self.assertEqual(data['is_direct_chat'], True)
        self.assertEqual(Chat.objects.first().title, chat_title_2)
        self.assertEqual(Chat.objects.first().is_direct_chat, True)

    def test_patch_chat_needs_auth(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            data={"title": chat_title_2},
            headers={
                "project-id": str(self.project.public_key),
                "user-name": '...',
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 403)

    def test_patch_chat_needs_to_be_your_project(self):
        temp_project = Project.objects.create(owner=self.user, title=project_title_1)
        temp_person = Person.objects.create(username=user_email_2, secret=user_password_2, project=temp_project)
        temp_chat = Chat.objects.create(project=temp_project, admin=temp_person, title=chat_title_2)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/'.format(str(temp_chat.pk)),
            data={"title": chat_title_2},
            headers={
                "project-id": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)


class DeleteChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)

    def test_delete_chat(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Chat.objects.all()), 0)

    def test_delete_chat_with_chat_auth(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_delete_chat_needs_auth(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/'.format(str(self.chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": '...',
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_delete_chat_needs_to_be_your_project(self):
        temp_project = Project.objects.create(owner=self.user, title=project_title_1)
        temp_person = Person.objects.create(username=user_email_2, secret=user_password_2, project=temp_project)
        temp_chat = Chat.objects.create(project=temp_project, admin=temp_person, title=chat_title_2)

        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/'.format(str(temp_chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Chat.objects.all()), 2)
