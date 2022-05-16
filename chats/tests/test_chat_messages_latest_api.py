from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat, Message
from projects.models import User, Project

USER_1 = 'adam@gmail.com'
PASSWORD = 'potato_123'

USER_2 = 'adam2@gmail.com'

PROJECT = "Chat Engine"
CHAT_TITLE = "Chat Engine"


class GetChatsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_1, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER_1, secret=PASSWORD)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_TITLE)
        self.message_1 = Message.objects.create(chat=self.chat, sender=self.person, text='...1')
        self.message_2 = Message.objects.create(chat=self.chat, sender=self.person, text='...2')

    def test_get_chats(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/latest/{}/'.format(str(self.chat.id), '1'),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['id'], self.message_2.id)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/latest/{}/'.format(str(self.chat.id), '2'),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['id'], self.message_1.id)
        self.assertEqual(data[1]['id'], self.message_2.id)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/latest/{}/'.format(str(self.chat.id), '3'),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['id'], self.message_1.id)
        self.assertEqual(data[1]['id'], self.message_2.id)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/latest/{}/'.format(str(self.chat.id), '0'),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_1,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 0)

    def test_get_chats_needs_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/latest/{}/'.format(str(self.chat.id), '0'),
            headers={}
        )

        self.assertEqual(response.status_code, 403)

    def test_get_chats_needs_to_be_a_chat_person(self):
        Person.objects.create(project=self.project, username=USER_2, secret=PASSWORD)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/latest/{}/'.format(str(self.chat.id), '1'),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_2,
                "user-secret": PASSWORD
            }
        )

        self.assertEqual(response.status_code, 404)
