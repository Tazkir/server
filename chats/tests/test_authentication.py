from rest_framework.test import APITestCase, APIRequestFactory

from chats.models import Person, Chat

from projects.models import User, Project

from chats.authentication import ChatAccessKeyAuthentication

EMAIL = 'test@mail.co'
PASSWORD = 'testpass1234'

TEMP_EMAIL = 'test@mail.com'

PROJECT = 'Test Project'
CHAT = 'Test Chat'


class ChatAccessKeyAuthenticationTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=EMAIL, secret=PASSWORD)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)

        self.factory = APIRequestFactory()
        self.request = self.factory.get(f'/chats/{str(self.chat.id)}')
        self.authenticator = ChatAccessKeyAuthentication()

    def test_public_key(self):
        self.request.headers = {
            "project-id": str(self.project.public_key),
            "access-key": self.chat.access_key,
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response[0].title, self.chat.title)
        self.assertEqual(response[1].title, self.project.title)

    def test_public_key_needs_access_key(self):
        self.request.headers = {
            "project-id": str(self.project.public_key),
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response, None)

    def test_private_key(self):
        self.request.headers = {
            "private-key": str(self.project.private_key),
        }
        response = self.authenticator.authenticate(self.request)
        self.assertEqual(response[0].title, self.chat.title)
        self.assertEqual(response[1].title, self.project.title)
