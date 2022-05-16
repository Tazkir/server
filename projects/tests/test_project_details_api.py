from rest_framework.authtoken.models import Token
from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, RequestsClient, force_authenticate

from projects.models import User, Project
from projects.views import ProjectDetails

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'eve@gmail.com'
user_password_2 = 'guacamole_123'

project_title_1 = "Chat Engine 1"
project_title_2 = "Chat Engine 2"


class GetProjectDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.client = RequestsClient()

    def test_get_projects(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['owner'], user_email_1)
        self.assertEqual(data['title'], project_title_1)
        self.assertEqual(data['is_active'], True)

    def test_get_projects_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token '}
        )

        self.assertEqual(response.status_code, 403)

    def test_get_projects_needs_to_be_yours(self):
        temp_user = User.objects.create_user(email=user_email_2, password=user_password_2)
        temp_token = Token.objects.create(user=temp_user)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)


class PatchProjectDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.client = RequestsClient()

    def test_patch_your_project(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            json={"title": project_title_2},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], project_title_2)

    def test_patch_your_project_notification(self):
        is_emails_enabled = True
        email_sender = 'adam@mail.co'
        email_link = 'https://mail.co/redirect/'

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            json={
                "is_emails_enabled": is_emails_enabled,
                "email_sender": email_sender,
                "email_link": email_link
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['is_emails_enabled'], is_emails_enabled)
        self.assertEqual(data['email_sender'], email_sender)
        self.assertEqual(data['email_link'], email_link)

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            json={
                "is_emails_enabled": is_emails_enabled,
                "email_sender": email_sender,
                "email_link": 'example'
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 400)

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            json={
                "is_emails_enabled": is_emails_enabled,
                "email_sender": 'example',
                "email_link": email_link
            },
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 400)

    def test_patch_your_project_do_nothing(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            json={},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], project_title_1)

    def test_patch_your_project_needs_auth(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            json={},
        )

        self.assertEqual(response.status_code, 403)

    def test_patch_your_project_needs_to_be_yours(self):
        temp_user = User.objects.create_user(email=user_email_2, password=user_password_2)
        temp_token = Token.objects.create(user=temp_user)

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            json={},
            headers={"Authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)


class DeleteProjectDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.client = RequestsClient()

    def test_delete_your_project(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Project.objects.all()), 0)

    def test_delete_your_project_needs_auth(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token... {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Project.objects.all()), 1)

    def test_delete_your_project_needs_to_be_yours(self):
        temp_user = User.objects.create_user(email=user_email_2, password=user_password_2)
        temp_token = Token.objects.create(user=temp_user)

        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Project.objects.all()), 1)
