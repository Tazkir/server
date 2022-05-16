from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person

from projects.models import User, Project

USER_1 = 'adam@gmail.com'
USER_2 = 'eve@gmail.com'
USER_3 = 'joe@gmail.com'
PASSWORD = 'potato_123'

PROJECT = "Chat Engine Project 1"
CHAT = "Chat Engine Chat 1"


class GetPeoplePrivateTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER_1, secret=PASSWORD)
        self.client = RequestsClient()

    def test_get_people(self):
        response = self.client.get(
            'http://127.0.0.1:8000/users',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)

        response = self.client.get(
            'http://127.0.0.1:8000/users/',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)

    def test_get_people_with_params(self):
        response = self.client.get(
            'http://127.0.0.1:8000/users?page=1',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        response = self.client.get(
            'http://127.0.0.1:8000/users/?page=0',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)

        response = self.client.get(
            'http://127.0.0.1:8000/users/?page=0&page_size=0',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        Person.objects.create(project=self.project, username=USER_2, secret=PASSWORD)
        Person.objects.create(project=self.project, username=USER_3, secret=PASSWORD)
        response = self.client.get(
            'http://127.0.0.1:8000/users/?page=0&page_size=2',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_get_people_needs_private_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/users',
            headers={"private-key": '...'}
        )
        self.assertEqual(response.status_code, 403)

    def test_get_people_not_public_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/users',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 403)


class PostPersonPrivateTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER_1, secret=PASSWORD)
        self.client = RequestsClient()

    def test_post_person(self):
        response = self.client.post(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['email'], USER_2)
        self.assertEqual(data['username'], USER_2)

        response = self.client.post(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 400)

    def test_post_person_needs_private_auth(self):
        response = self.client.post(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={"private-key": '.'}
        )
        self.assertEqual(response.status_code, 403)

    def test_post_person_not_public_auth(self):
        response = self.client.post(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 403)


class PutPersonPrivateTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER_1, secret=PASSWORD)
        self.client = RequestsClient()

    def test_put_create_then_get_person(self):
        response = self.client.put(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['email'], USER_2)
        self.assertEqual(data['username'], USER_2)

        response = self.client.put(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['email'], USER_2)
        self.assertEqual(data['username'], USER_2)

    def test_put_person_needs_private_auth(self):
        response = self.client.put(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={"private-key": '.'}
        )
        self.assertEqual(response.status_code, 403)

    def test_post_person_not_public_auth(self):
        response = self.client.put(
            'http://127.0.0.1:8000/users',
            data={
                "username": USER_2,
                "email": USER_2,
                "secret": PASSWORD,
                "is_online": True,
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 403)
