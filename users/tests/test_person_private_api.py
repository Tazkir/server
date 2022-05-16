from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat

from projects.models import User, Project

USER_1 = 'adam@gmail.com'
USER_2 = 'eve@gmail.com'
PASSWORD = 'potato_123'

PROJECT = "Chat Engine Project 1"
CHAT = "Chat Engine Chat 1"


class GetPersonPrivateTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER_1, secret=PASSWORD)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)

    def test_get_person(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['email'], '')
        self.assertEqual(data['username'], USER_1)
        self.assertEqual(data['is_online'], False)

    def test_get_person_needs_private_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={"private-key": ''}
        )
        self.assertEqual(response.status_code, 403)

    def test_get_person_not_public_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 403)

    def test_get_person_not_another_project(self):
        temp_project = Project.objects.create(owner=self.user, title=PROJECT)
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={"private-key": str(temp_project.private_key)}
        )
        self.assertEqual(response.status_code, 404)


class PatchPersonPrivateTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER_1, secret=PASSWORD)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)

    def test_patch_person(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            data={'email': USER_2, 'is_online': True},
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['email'], USER_2)
        self.assertEqual(data['username'], USER_1)
        self.assertEqual(data['is_online'], True)

    def test_patch_person_needs_private_auth(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            data={'email': USER_2, 'is_online': True},
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_person_not_public_auth(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            data={'email': USER_2, 'is_online': True},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 403)

    def test_patch_person_not_another_project(self):
        temp_project = Project.objects.create(owner=self.user, title=PROJECT)
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            data={'email': USER_2, 'is_online': True},
            headers={"private-key": str(temp_project.private_key)}
        )
        self.assertEqual(response.status_code, 404)


class DeletePersonPrivateTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER_1, secret=PASSWORD)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)

    def test_delete_person(self):
        self.assertEqual(len(Person.objects.all()), 1)

        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Person.objects.all()), 0)

        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 404)

    def test_delete_person_needs_private_auth(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk))
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Person.objects.all()), 1)

    def test_delete_person_not_public_auth(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Person.objects.all()), 1)

    def test_delete_person_not_another_project(self):
        temp_project = Project.objects.create(owner=self.user, title=PROJECT)
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/users/{}/'.format(str(self.person.pk)),
            headers={"private-key": str(temp_project.private_key)}
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Person.objects.all()), 1)
