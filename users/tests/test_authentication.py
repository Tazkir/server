from rest_framework.test import APITestCase, APIRequestFactory

from chats.models import Person, Chat

from projects.models import User, Project

from users.authentication import UserSecretAuthentication

EMAIL = 'test@mail.co'
PASSWORD = 'testpass1234'

TEMP_EMAIL = 'test@mail.com'

PROJECT = 'Test Project'
CHAT = 'Test Chat'


class UserSecretAuthenticationTestCase(APITestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.request = self.factory.get('/chats/')
        self.authenticator = UserSecretAuthentication()

        self.user = User.objects.create_user(email=EMAIL, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=EMAIL, secret=PASSWORD)

    def test_public_key(self):
        self.request.headers = {
            "project-id": str(self.project.public_key),
            "user-name": EMAIL,
            "user-secret": PASSWORD,
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response[0].username, self.person.username)
        self.assertEqual(response[1].title, self.project.title)

    def test_public_key_needs_user_name(self):
        self.request.headers = {
            "project-id": str(self.project.public_key),
            "user-secret": PASSWORD,
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response, None)

    def test_public_key_needs_user_secret(self):
        self.request.headers = {
            "project-id": str(self.project.public_key),
            "user-name": EMAIL,
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response, None)

    def test_private_key(self):
        self.request.headers = {
            "private-key": str(self.project.private_key)
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response[0].username, self.person.username)
        self.assertEqual(response[1].title, self.project.title)

    def test_private_key_with_user_name(self):
        temp_person = Person.objects.create(project=self.project, username=TEMP_EMAIL, secret=PASSWORD)
        self.request.headers = {
            "private-key": str(self.project.private_key),
            "user-name": TEMP_EMAIL,
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response[0].username, temp_person.username)
        self.assertEqual(response[1].title, self.project.title)

    def test_private_key_with_chat_id(self):
        temp_person = Person.objects.create(project=self.project, username=TEMP_EMAIL, secret=PASSWORD)
        chat = Chat.objects.create(project=self.project, admin=temp_person, title=CHAT)
        request = self.factory.get(f'/chats/{str(chat.id)}/')
        request.headers = {
            "private-key": str(self.project.private_key)
        }
        response = self.authenticator.authenticate(request)
        self.assertEqual(response[0].username, temp_person.username)
        self.assertEqual(response[1].title, self.project.title)

    def test_private_key_user_name_overrides_chat_id(self):
        temp_person = Person.objects.create(project=self.project, username=TEMP_EMAIL, secret=PASSWORD)
        chat = Chat.objects.create(project=self.project, admin=temp_person, title=CHAT)
        request = self.factory.get(f'/chats/{str(chat.id)}/')
        request.headers = {
            "private-key": str(self.project.private_key),
            "user-name": self.person.username,
        }
        response = self.authenticator.authenticate(request)
        self.assertEqual(response[0].username, self.person.username)
        self.assertEqual(response[1].title, self.project.title)

    def test_private_key_gets_first_chat_user(self):
        Person.objects.create(project=self.project, username=TEMP_EMAIL, secret=PASSWORD)
        self.request.headers = {
            "private-key": str(self.project.private_key),
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response[0].username, self.person.username)
        self.assertEqual(response[1].title, self.project.title)

    def test_private_key_no_chat_users(self):
        Person.objects.all().delete()
        self.request.headers = {
            "private-key": str(self.project.private_key)
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response[0], None)
        self.assertEqual(response[1].title, self.project.title)
