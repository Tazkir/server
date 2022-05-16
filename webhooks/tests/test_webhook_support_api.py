from django.test import tag

from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory

from chats.models import Person, Chat, Message
from chats.serializers import ChatSerializer, MessageSerializer

from projects.models import User, Project
from projects.serializers import ProjectSerializer, PersonPublicSerializer

from webhooks.models import Webhook
from webhooks.views import Webhooks
from webhooks.sender import WebhookSerializer


USER_EMAIL = 'alamorre@gmail.com'
USER_PASSWORD = 'potato_123'

PROJECT_1 = "Engine 1"

TRIGGER = 'On New Message'
URL = 'http://127.0.0.1:8000/webhooks/test/'

CHAT = 'adam@lamorre.co'


class GetProjectChatTestCase(APITestCase):
    @tag('server_must_run')
    def test_send_webhook_for_email_notifications(self):
        user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        project = Project.objects.create(owner=user, title=PROJECT_1)
        person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=project)
        webhook = Webhook.objects.create(project=project, event_trigger=TRIGGER, url=URL)
        chat = Chat.objects.create(project=project, admin=person, title=CHAT)

        project_json = ProjectSerializer(project, many=False).data
        webhook_json = WebhookSerializer(webhook, many=False).data
        chat_json = ChatSerializer(chat, many=False).data
        person_json = PersonPublicSerializer(person, many=False).data

        message = Message.objects.create(chat=chat, sender=person, text='From admin to user', sender_username=USER_EMAIL)
        message_json = MessageSerializer(message, many=False).data

        data = {
            "project": project_json,
            "webhook": webhook_json,
            "chat": chat_json,
            "person": person_json,
            "message": message_json
        }
        factory = APIRequestFactory()
        view = Webhooks.as_view()
        request = factory.post(
            '/webhooks/',
            json.dumps(data),
            content_type='application/json'
        )
        view(request)

        message = Message.objects.create(chat=chat, text='From user to admin', sender_username=CHAT)
        message_json = MessageSerializer(message, many=False).data

        data = {
            "project": project_json,
            "webhook": webhook_json,
            "chat": chat_json,
            "person": person_json,
            "message": message_json
        }
        factory = APIRequestFactory()
        view = Webhooks.as_view()
        request = factory.post(
            '/webhooks/',
            json.dumps(data),
            content_type='application/json'
        )
        view(request)
