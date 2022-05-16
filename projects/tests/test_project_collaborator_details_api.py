from rest_framework.utils import json
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate, RequestsClient

from projects.models import User, Project, Collaborator
from projects.views import CollaboratorsDetailsWeb

USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

PROJECT_1 = "Chat Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'


class GetProjectCollaboratorTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.collaborator = Collaborator.objects.get(user=self.user, project=self.project)
        self.client = RequestsClient()

    def test_get_project_collaborator(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user'], USER_EMAIL)
        self.assertEqual(data['role'], 'admin')

    def test_get_project_collaborator_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
        )

        self.assertEqual(response.status_code, 403)

    def test_get_project_collaborator_must_be_a_collaborator(self):
        temp_user = User.objects.create(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_token = Token.objects.create(user=temp_user)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
            headers={"authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)


class PatchProjectCollaboratorTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.collaborator = Collaborator.objects.get(user=self.user, project=self.project)
        self.client = RequestsClient()

    def test_patch_project_collaborator(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
            json={"role": 'member'},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user'], USER_EMAIL)
        self.assertEqual(data['role'], 'member')

    def test_patch_project_collaborator_needs_auth(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
            json={"role": 'member'},
        )

        self.assertEqual(response.status_code, 403)

    def test_patch_project_collaborator_must_be_admin(self):
        temp_user = User.objects.create(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_token = Token.objects.create(user=temp_user)
        Collaborator.objects.create(user=temp_user, project=self.project, role='not admin')

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
            json={"role": 'member'},
            headers={"authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)


class DeleteProjectCollaboratorTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.collaborator = Collaborator.objects.get(user=self.user, project=self.project)
        self.client = RequestsClient()

    def test_delete_project_collaborator(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(len(Collaborator.objects.all()), 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['user'], USER_EMAIL)
        self.assertEqual(data['role'], 'admin')

    def test_delete_project_collaborator_needs_auth(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
        )

        self.assertEqual(response.status_code, 403)

    def test_delete_project_collaborator_must_be_admin(self):
        temp_user = User.objects.create(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_token = Token.objects.create(user=temp_user)
        Collaborator.objects.create(user=temp_user, project=self.project, role='not admin')

        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/collaborators/{}/'.format(self.project.pk, str(self.collaborator.id)),
            headers={"authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)
