from django.test import tag

from chats.serializers import ChatSerializer, MessageSerializer
from projects.serializers import PersonSerializer, ProjectSerializer
from rest_framework.test import APITestCase

from chats.models import Person, Chat, Message

from projects.models import User, Project

from webhooks.models import Webhook
from webhooks.sender import hook


USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

PROJECT_1 = "Engine 1"

TRIGGER = 'On New Message'
URL = 'http://127.0.0.1:8000/webhooks/test/'

CHAT = 'Chat 1'

MESSAGE = 'Hello'


class GetProjectChatTestCase(APITestCase):
    @tag('server_must_run')
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=self.project)
        self.webhook = Webhook.objects.create(project=self.project, event_trigger=TRIGGER, url=URL)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)
        self.message = Message.objects.create(chat=self.chat, sender=self.person, text=MESSAGE)

    @tag('server_must_run')
    def test_send_hooks_with_data_and_404s(self):
        project_json = ProjectSerializer(self.project, many=False).data
        response, data = hook.post(event_trigger=TRIGGER, project_json=project_json, timeout=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['project']['public_key'], str(self.project.public_key))
        self.assertEqual(data['webhook']['event_trigger'], self.webhook.event_trigger)
        self.assertEqual(data['webhook']['url'], self.webhook.url)
        self.assertEqual(len(data['webhook']['secret']), 40)

        person_json = PersonSerializer(self.person).data
        response, data = hook.post(event_trigger=TRIGGER, project_json=project_json, person_json=person_json, timeout=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['person']['username'], self.person.username)

        chat_json = ChatSerializer(self.chat).data
        response, data = hook.post(event_trigger=TRIGGER, project_json=project_json, chat_json=chat_json, timeout=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['chat']['title'], self.chat.title)

        message_json = MessageSerializer(self.message).data
        response, data = hook.post(event_trigger=TRIGGER, project_json=project_json, message_json=message_json, timeout=1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message']['text'], self.message.text)

        response, data = hook.post(event_trigger='...', project_json=project_json, message_json=message_json, timeout=1)
        self.assertEqual(response, None)
        self.assertEqual(data, None)
