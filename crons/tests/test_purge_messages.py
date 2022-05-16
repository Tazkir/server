from datetime import datetime, timedelta
import pytz

from rest_framework.test import APITestCase, RequestsClient

from accounts.models import User
from chats.models import Person, Chat, Message
from projects.models import Project

USER = 'adam@mail.co'
PASS = 'pass1234'

PROJECT = 'Project'
CHAT = 'Chat'
MESSAGE = 'Hello world.'


class PurgeMessagesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email=USER, password=PASS)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER, secret=PASS)
        self.chat = Chat.objects.create(admin=self.person, project=self.project, title=CHAT)
        self.message_1 = Message.objects.create(sender=self.person, chat=self.chat, text=MESSAGE)
        self.message_2 = Message.objects.create(sender=self.person, chat=self.chat, text=MESSAGE)

    def test_purge_one_of_two_messages(self):
        utc = pytz.UTC
        now = datetime.now().replace(tzinfo=utc)

        message = Message.objects.first()
        message.created = now - timedelta(days=self.project.message_history + 1)
        message.save()

        self.assertEqual(len(Message.objects.all()), 2)

        client = RequestsClient()
        response = client.get('http://127.0.0.1:8000/crons/purge_old_messages')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Message.objects.all()), 1)
