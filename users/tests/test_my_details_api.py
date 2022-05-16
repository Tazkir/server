from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat

from projects.models import User, Project

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'eve@gmail.com'

project_title_1 = "Chat Engine Project 1"

chat_title_1 = "Chat Engine Chat 1"


class GetMyDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)
        self.client = RequestsClient()

    def test_get_my_person(self):       
        response = self.client.get(
            'http://127.0.0.1:8000/users/me/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_1)
        self.assertEqual(data['is_online'], False)

    def test_get_my_person_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/users/me/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1
            }
        )

        self.assertEqual(response.status_code, 403)


class PatchMyDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)
        self.client = RequestsClient()

    def test_patch_my_person(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/users/me/',
            data={
                "username": user_email_2,
                "is_online": True
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_2)
        self.assertEqual(data['is_online'], True)

    def test_get_my_person_needs_auth(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/users/me/',
            data={
                "username": user_email_2,
                "is_online": True
            },
            headers={
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 403)

class DeleteMyDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)
        self.client = RequestsClient()

    def test_delete_my_person(self):
        self.assertEqual(len(Person.objects.all()), 1)

        response = self.client.delete(
            'http://127.0.0.1:8000/users/me/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_1)
        self.assertEqual(len(Person.objects.all()), 0)

    def test_get_my_person_needs_auth(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/users/me/',
            headers={
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Person.objects.all()), 1)
