from rest_framework.authtoken.models import Token
from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, RequestsClient, force_authenticate

from chats.models import Person
from projects.models import User, Project

from projects.views import PersonDetailsWeb

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'eve@gmail.com'
user_password_2 = 'pretzel_123'

project_title_1 = "Chat Engine 1"

first_name = 'Adam'
last_name = 'La Morre'


class GetProjectPersonWebTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)
        self.client = RequestsClient()

    def test_get_person(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/people/{}/'.format(str(self.project.pk), str(self.person.id)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_1)
        self.assertNotEqual(data['secret'], user_password_1)

    def test_get_person_needs_auth(self):
        factory = APIRequestFactory()
        view = PersonDetailsWeb.as_view()
        request = factory.get(
            '/projects/people/{}/'.format(str(self.person.pk))
        )
        response = view(request, project_id=self.project.public_key, person_id=self.person.pk)

        self.assertEqual(response.status_code, 403)


class PatchProjectPersonWebTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)
        self.client = RequestsClient()

    def test_patch_person(self):
        old_password = self.person.secret

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/people/{}/'.format(str(self.project.pk), str(self.person.id)),
            json={
                "username": user_email_2,
                'email': user_email_2,
                'first_name': first_name,
                'last_name': last_name
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_2)
        self.assertEqual(data['email'], user_email_2)
        self.assertEqual(data['first_name'], first_name)
        self.assertEqual(data['last_name'], last_name)
        self.assertEqual(data['secret'], old_password)
        self.assertEqual(data['is_online'], False)

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/people/{}/'.format(str(self.project.pk), str(self.person.id)),
            json={
                "username": user_email_2,
                "secret": user_password_2,
                "is_online": True
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['is_online'], True)
        self.assertEqual(data['username'], user_email_2)
        self.assertNotEqual(data['secret'], old_password)
        self.assertNotEqual(data['secret'], user_password_2)

    def test_patch_person_cannot_use_another_username(self):
        person = Person.objects.create(username='adam', secret=user_password_1, project=self.project)

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/people/{}/'.format(str(self.project.pk), str(self.person.id)),
            json={"username": person.username},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)

    def test_patch_person_needs_auth(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/people/{}/'.format(str(self.project.pk), str(self.person.id)),
            json={
                "username": user_email_2,
                "secret": user_password_2,
                "is_online": True
            },
        )

        self.assertEqual(response.status_code, 403)


class DeleteProjectPersonWebTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)
        self.client = RequestsClient()

    def test_delete_person(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/people/{}/'.format(str(self.project.pk), str(self.person.id)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Person.objects.all()), 0)

    def test_delete_person_needs_auth(self):
        factory = APIRequestFactory()
        view = PersonDetailsWeb.as_view()
        request = factory.delete('/projects/people/')
        response = view(request, project_id=self.project.public_key, person_id=self.person.pk)

        self.assertEqual(response.status_code, 403)
