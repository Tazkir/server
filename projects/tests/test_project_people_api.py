from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person
from projects.models import User, Project

USER = 'adam@gmail.com'
USER_2 = 'adam2@gmail.com'
USER_3 = 'adam3@gmail.com'
PASSWORD = 'potato_123'

FIRST_NAME = 'Adam'
LAST_NAME = 'La Morre'

PROJECT = "Chat Engine 1"


class GetProjectPeopleTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(username=USER, secret=PASSWORD, project=self.project)
        self.client = RequestsClient()

    def test_get_projects(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/people/',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)

    def test_get_projects_with_params(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/people/?page=1',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/people/?page=0&page_size=0',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        Person.objects.create(username=USER_2, secret=PASSWORD, project=self.project)
        Person.objects.create(username=USER_3, secret=PASSWORD, project=self.project)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/people/?page=0&page_size=2',
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_get_projects_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/people/',
            headers={"private-key": '...'}
        )
        self.assertEqual(response.status_code, 403)


class PostProjectPersonTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.client = RequestsClient()

    def test_post_project_person(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/people/',
            data={
                'username': USER,
                'secret': PASSWORD,
                'email': USER,
                'first_name': FIRST_NAME,
                'last_name': LAST_NAME,
                "custom_json": json.dumps({"this": "that"})
            },
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Person.objects.all()), 1)
        self.assertEqual(data['username'], USER)
        self.assertEqual(data['first_name'], FIRST_NAME)
        self.assertEqual(data['last_name'], LAST_NAME)
        self.assertEqual(data['email'], USER)
        self.assertNotEqual(data['secret'], PASSWORD)
        self.assertEqual(json.loads(data['custom_json'])['this'], "that")

    def test_post_person_cannot_use_another_username(self):
        person = Person.objects.create(username='adam', secret=PASSWORD, project=self.project)
        response = self.client.post(
            'http://127.0.0.1:8000/projects/people/',
            data={'username': person.username, 'secret': PASSWORD},
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 400)

    def test_post_project_person_needs_auth(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/people/',
            data={'username': USER, 'secret': PASSWORD},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Person.objects.all()), 0)

    def test_post_project_person_needs_username(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/people/',
            data={'secret': PASSWORD},
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Person.objects.all()), 0)

    def test_post_project_person_needs_secret(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/people/',
            data={'username': USER},
            headers={"private-key": str(self.project.private_key)}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Person.objects.all()), 0)
