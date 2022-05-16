from rest_framework.authtoken.models import Token
from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate, RequestsClient

from projects.models import Collaborator, User, Project, Invite
from projects.views import ProjectInvitesWeb

USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

PROJECT_1 = "Chat Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'


class GetProjectInvitesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.new_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.invite = Invite.objects.create(to_email=self.new_user.email, project=self.project, role='admin')
        self.client = RequestsClient()

    def test_get_project_invites(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['to_email'], USER_EMAIL_2)
        self.assertEqual(data[0]['role'], 'admin')
        self.assertEqual(len(data[0]['access_key']), 40)

    def test_get_project_invites_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
        )

        self.assertEqual(response.status_code, 403)

    def test_get_project_invites_must_be_a_collaborator(self):
        temp_user = User.objects.create(email='temp@mail.com', password='...')
        temp_token = Token.objects.create(user=temp_user)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(temp_token.key)}
        )

        self.assertEqual(response.status_code, 404)


class PostProjectInviteTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.new_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.client = RequestsClient()

    def test_post_project_invites(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
            json={"to_email": USER_EMAIL_2, "role": 'admin'},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['to_email'], USER_EMAIL_2)
        self.assertEqual(data['role'], 'admin')
        self.assertEqual(len(data['access_key']), 40)

    def test_post_project_invites_needs_auth(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
            json={"to_email": USER_EMAIL_2, "role": 'admin'},
        )

        self.assertEqual(response.status_code, 403)

    def test_post_project_invites_must_be_admin(self):
        collaborator = Collaborator.objects.first()
        collaborator.role = 'member'
        collaborator.save()

        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
            json={"to_email": USER_EMAIL_2, "role": 'admin'},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 404)

    def test_post_project_invites_needs_to_email(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
            json={"role": 'admin'},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)

    def test_post_project_invites_needs_role(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/invites/'.format(str(self.project.public_key)),
            json={"to_email": USER_EMAIL_2},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)
