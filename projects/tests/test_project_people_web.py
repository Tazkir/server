from rest_framework.utils import json
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate, RequestsClient

from chats.models import Person
from projects.models import User, Project

from projects.views import ProjectPeopleWeb

USER_1 = 'adam@gmail.com'
USER_2 = 'adam2@gmail.com'
USER_3 = 'adam3@gmail.com'
PASSWORD = 'potato_123'

first_name = 'Adam'
last_name = 'La Morre'

PROJECT = "Chat Engine 1"


class GetProjectPeopleWebTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(username=USER_1, secret=PASSWORD, project=self.project)
        self.client = RequestsClient()

    def test_get_projects_people(self):
        token = Token.objects.get_or_create(user=self.user)
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/people/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(token[0].key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)

    def test_get_project_people_with_params(self):
        token = Token.objects.get_or_create(user=self.user)
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/people/?page=1'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(token[0].key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/people/?page=0&page_size=0'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(token[0].key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        Person.objects.create(username=USER_2, secret=PASSWORD, project=self.project)
        Person.objects.create(username=USER_3, secret=PASSWORD, project=self.project)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/people/?page=0&page_size=2'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(token[0].key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)

    def test_get_projects_people_needs_auth(self):
        factory = APIRequestFactory()
        view = ProjectPeopleWeb.as_view()
        request = factory.get('/projects/people/')
        response = view(request, project_id=self.project.public_key)

        self.assertEqual(response.status_code, 403)


class PostProjectPersonWebTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.client = RequestsClient()

    def test_post_project_person(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/people/'.format(self.project.public_key),
            json={
                'username': USER_1,
                'secret': PASSWORD,
                "email": USER_1,
                'first_name': first_name,
                'last_name': last_name,
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Person.objects.all()), 1)
        self.assertEqual(data['username'], USER_1)
        self.assertEqual(data['email'], USER_1)
        self.assertEqual(data['first_name'], first_name)
        self.assertEqual(data['last_name'], last_name)
        self.assertNotEqual(data['secret'], PASSWORD)

    def test_post_person_cannot_use_another_username(self):
        person = Person.objects.create(username='adam', secret=PASSWORD, project=self.project)

        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/people/'.format(self.project.public_key),
            json={"username": person.username, 'secret': PASSWORD},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)

    def test_post_project_person_needs_auth(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/people/'.format(self.project.public_key),
            json={
                'username': USER_1,
                'secret': PASSWORD,
                'first_name': first_name,
                'last_name': last_name,
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Person.objects.all()), 0)

    def test_post_project_person_needs_username(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/people/'.format(self.project.public_key),
            json={
                'secret': PASSWORD,
                'first_name': first_name,
                'last_name': last_name,
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Person.objects.all()), 0)

    def test_post_project_person_needs_secret(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/people/'.format(self.project.public_key),
            json={
                'username': USER_1,
                'first_name': first_name,
                'last_name': last_name,
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Person.objects.all()), 0)
