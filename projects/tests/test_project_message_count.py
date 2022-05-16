from rest_framework.authtoken.models import Token
from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from projects.models import User, Project
from projects.views import MessageCount

from chats.models import Person, Chat, Message

USER_EMAIL = 'adam@gmail.com'
USER_PASS = 'potato_123'
PROJECT = "Chat Engine 1"


class GetProjectMessageCountTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASS)
        self.token = Token.objects.create(user=self.user)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.client = RequestsClient()

    def test_get_message_count(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/message_count/'.format(self.project.pk),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message_count'], 0)

        person = Person.objects.create(project=self.project, username=USER_EMAIL, secret=USER_PASS)
        chat = Chat.objects.create(project=self.project, admin=person, title=PROJECT)
        Message.objects.create(sender=person, chat=chat)
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/message_count/'.format(self.project.pk),
            headers={"Authorization": 'Token {}'.format(self.token.key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message_count'], 1)

    def test_get_message_count_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/projects/{}/message_count/'.format(self.project.pk)
        )

        self.assertEqual(response.status_code, 403)
