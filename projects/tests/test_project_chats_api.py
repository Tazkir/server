from rest_framework.utils import json
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat

from projects.models import User, Project

USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

USER_2 = 'adam2@gmail.com'
USER_3 = 'adam3@gmail.com'
PASSWORD = 'potato_123'

CHAT_TITLE = '123'
USERNAME = 'alamorre'

PROJECT_1 = "Chat Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'

PROJECT_2 = "Chat Engine 2"


class GetProjectChatsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=self.project)
        self.client = RequestsClient()

    def test_get_project_chats(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

    def test_get_projects_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(str(self.project.public_key)),
        )

        self.assertEqual(response.status_code, 403)

    def test_get_project_people_with_params(self):
        Chat.objects.create(project=self.project, admin=self.person, title='...')

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/chats/?page=1'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/chats/?page=0&page_size=0'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        Chat.objects.create(project=self.project, admin=self.person, title='...')
        Chat.objects.create(project=self.project, admin=self.person, title='...')

        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/chats/?page=0&page_size=2'.format(str(self.project.public_key)),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)


class PostProjectChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(project=self.project, username=USERNAME)
        self.client = RequestsClient()

    def test_post_project_chat(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(self.project.pk),
            json={"title": CHAT_TITLE, "admin_username": USERNAME},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['title'], CHAT_TITLE)
        self.assertEqual(data['admin']['username'], USERNAME)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_post_project_person_chat_title_optional(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(self.project.pk),
            json={"admin_username": USERNAME},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['title'], None)
        self.assertEqual(data['admin']['username'], USERNAME)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_post_project_person_needs_admin_username(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(self.project.pk),
            json={"title": CHAT_TITLE},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Chat.objects.all()), 0)

    def test_post_project_chat_needs_auth(self):
        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(self.project.pk),
            json={"title": CHAT_TITLE},
            headers={"nothing": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Chat.objects.all()), 0)

    def test_post_project_chat_cannot_be_another_project(self):
        temp_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)

        response = self.client.post(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(temp_project.pk),
            json={"title": CHAT_TITLE, "admin_username": USERNAME},
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Chat.objects.all()), 0)
