from rest_framework.authtoken.models import Token
from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from projects.models import User, Project

USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

PROJECT_1 = "Chat Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'


class GetProjectCollaboratorsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.client = RequestsClient()

    def test_get_project_collaborators(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/collaborators/'.format(self.project.pk),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['user'], USER_EMAIL)
        self.assertEqual(data[0]['role'], 'admin')

    def test_get_project_collaborators_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/collaborators/'.format(self.project.pk)
        )

        self.assertEqual(response.status_code, 403)

    def test_get_project_collaborators_must_be_a_collaborator(self):
        temp_user = User.objects.create(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_token = Token.objects.create(user=temp_user)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/collaborators/'.format(self.project.pk),
            headers={"Authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)
