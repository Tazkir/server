from rest_framework.authtoken.models import Token
from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, RequestsClient, force_authenticate

from projects.models import User, Project
from projects.views import ProjectDetails, PrivateKeyDetails

USER_EMAIL = 'adam@gmail.com'
USER_PASS = 'potato_123'

PROJECT = "Chat Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'

PROJECT_2 = "Chat Engine 2"


class GetProjectPrivateKeyTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASS)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.client = RequestsClient()

    def test_project_serializer_has_no_private_key(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/'.format(str(self.project.pk)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data.get('private_key', None), None)

    def test_get_project_private_key(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/private_key/'.format(str(self.project.pk)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['key'], str(self.project.private_key))

    def test_get_project_private_key_needs_auth(self):
        factory = APIRequestFactory()
        view = PrivateKeyDetails.as_view()
        request = factory.get('/projects/{}/private_key/'.format(self.project.pk))
        response = view(request, project_id=self.project.pk)

        self.assertEqual(response.status_code, 403)

    def test_get_project_private_key_cannot_be_another_project(self):
        temp_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/private_key/'.format(str(temp_project.pk)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 404)
