from rest_framework.utils import json
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate, RequestsClient

from chats.models import Person, Chat, ChatPerson

from projects.models import User, Project
from projects.views import ChatDetailsWeb

USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'
USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'

USERNAME = 'alamorre'

PROJECT_1 = "Chat Engine 1"
PROJECT_2 = "Chat Engine 2"

CHAT_TITLE = '123'
CHAT_TITLE_2 = '123'


class GetProjectChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=self.project)
        self.chat = Chat.objects.create(title=CHAT_TITLE, admin=self.person, project=self.project)
        self.client = RequestsClient()

    def test_get_project_chat_details(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(self.project.pk),
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 200)

    def test_get_projects_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/chats/'.format(self.project.pk),
        )

        self.assertEqual(response.status_code, 403)


class PatchProjectChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(project=self.project, username=USERNAME)
        self.chat = Chat.objects.create(title=CHAT_TITLE, admin=self.person, project=self.project)
        self.client = RequestsClient()

    def test_patch_project_chat(self):
        temp_person = Person.objects.create(project=self.project, username=USER_EMAIL_2, secret=USER_PASS_2)

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={
                "title": CHAT_TITLE_2, 'admin_username': temp_person.username
            },
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], CHAT_TITLE_2)
        self.assertEqual(data['admin']['username'], USER_EMAIL_2)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_patch_project_person_chat_title_nullable(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"title": None},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['title'], None)
        self.assertEqual(data['admin']['username'], self.person.username)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_patch_project_person_needs_admin_username(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"admin_username": None},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['admin']['username'], self.person.username)

    def test_patch_project_chat_needs_auth(self):
        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"admin_username": None},
            headers={"authorization": 'Token ...'}
        )

        self.assertEqual(response.status_code, 403)

    def test_patch_project_chat_cannot_be_another_project(self):
        temp_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)
        temp_person = Person.objects.create(project=temp_project, username=USER_EMAIL_2)
        temp_chat = Chat.objects.create(title=CHAT_TITLE, admin=temp_person, project=temp_project)

        response = self.client.patch(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(temp_chat.pk)),
            json={"title": '...'},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 404)


class PutProjectChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(project=self.project, username=USERNAME)
        self.person_2 = Person.objects.create(project=self.project, username=USER_EMAIL_2)
        self.chat = Chat.objects.create(title=CHAT_TITLE, admin=self.person, project=self.project)
        self.client = RequestsClient()

    def test_put_two_then_one_people(self):
        response = self.client.put(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"people": [{'person': USER_EMAIL_2}, {'person': USERNAME}]},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(ChatPerson.objects.all()), 2)

        response = self.client.put(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"people": [{'person': USER_EMAIL_2}]},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(ChatPerson.objects.all()), 1)

    def test_put_empty_list(self):
        response = self.client.put(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"people": []},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(ChatPerson.objects.all()), 0)

    def test_put_people_object_attempt(self):
        response = self.client.put(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"people": 'okok'},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(ChatPerson.objects.all()), 1)

    def test_put_bad_usernames_attempt(self):
        response = self.client.put(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            json={"people": ['not a user']},
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(ChatPerson.objects.all()), 1)


class DeleteProjectChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(project=self.project, username=USERNAME)
        self.chat = Chat.objects.create(title=CHAT_TITLE, admin=self.person, project=self.project)
        self.client = RequestsClient()

    def test_delete_project_chat(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Chat.objects.all()), 0)

    def test_delete_project_chat_needs_auth(self):
        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(self.chat.pk)),
            headers={"authorization": 'tok {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_delete_project_chat_cannot_be_another_project(self):
        temp_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)
        temp_person = Person.objects.create(project=temp_project, username=USER_EMAIL_2, secret=USER_PASS_2)
        temp_chat = Chat.objects.create(admin=temp_person, project=temp_project, title=CHAT_TITLE_2)

        response = self.client.delete(
            'http://127.0.0.1:8000/projects/{}/chats/{}/'.format(self.project.pk, str(temp_chat.pk)),
            headers={"authorization": 'Token {}'.format(self.token.key)}
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Chat.objects.all()), 2)
