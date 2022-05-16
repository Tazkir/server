import io
from PIL import Image

from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat, ChatPerson, Message
from projects.models import User, Project

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'eve@gmail.com'
user_password_2 = 'pretzel_123'

project_title_1 = "Chat Engine Project 1"
project_title_2 = "Chat Engine Project 2"

chat_title_1 = "Chat Engine"
message_1 = 'Hello world'
message_2 = 'Bye world!'
created = "2021-08-03 00:16:47.323962+00:00"


class GetMessagesTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)
        self.message = Message.objects.create(chat=self.chat, sender=self.person, text=message_1)
        self.message_2 = Message.objects.create(chat=self.chat, sender=self.person, text=message_2)

    def test_get_chat_messages(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['text'], message_1)
        self.assertEqual(data[1]['text'], message_2)

    def test_get_chat_messages_with_chat_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['text'], message_1)
        self.assertEqual(data[1]['text'], message_2)

    def test_get_chat_messages_another_chat_person(self):
        temp_person = Person.objects.create(project=self.project, username=user_email_2, secret=user_password_2)
        ChatPerson.objects.create(chat=self.chat, person=temp_person)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 2)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['text'], message_1)
        self.assertEqual(data[1]['text'], message_2)

    def test_get_chat_messages_must_be_your_project(self):
        ChatPerson.objects.all().delete()

        temp_project = Project.objects.create(owner=self.user, title=project_title_2)
        Person.objects.create(project=temp_project, username=user_email_2, secret=user_password_2)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            headers={
                "public-key": str(temp_project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_get_chat_messages_must_be_chat_person(self):
        ChatPerson.objects.all().delete()

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_get_chat_messages_needs_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            headers={}
        )

        self.assertEqual(response.status_code, 403)


class PostMessageTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)

    def test_post_chat_message(self):
        old_chat_updated = ChatPerson.objects.get(chat=self.chat, person=self.person).chat_updated

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            data={
                "text": message_1,
                "custom_json": json.dumps({"this": "that"}),
                "created": created
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)

        self.assertEqual(data['text'], message_1)
        self.assertEqual(json.loads(data['custom_json'])['this'], "that")
        self.assertEqual(data['sender']['username'], user_email_1)
        self.assertEqual(data['sender_username'], user_email_1)
        self.assertEqual(data['created'], created)
        self.assertEqual(len(data['attachments']), 0)
        self.assertEqual(len(Message.objects.all()), 1)

        chat_person = ChatPerson.objects.get(chat=self.chat, person=self.person)
        self.assertNotEqual(chat_person.chat_updated, old_chat_updated)
        self.assertEqual(str(chat_person.chat_updated), data['created'])

        # Test message was read by sender
        chat_person = ChatPerson.objects.get(chat=self.chat, person=self.person)
        self.assertEqual(data['id'], chat_person.last_read.pk)

    def test_post_chat_message_with_chat_auth(self):
        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            data={"text": message_1, 'sender_username': user_email_2},
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.pk),
                "access-key": self.chat.access_key
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)

        self.assertEqual(data['text'], message_1)
        self.assertEqual(data['sender'], None)
        self.assertEqual(data['sender_username'], user_email_2)
        self.assertEqual(len(data['attachments']), 0)
        self.assertEqual(len(Message.objects.all()), 1)

    def test_post_chat_message_with_mask(self):
        mask_username = 'adam!'
        file = io.BytesIO()
        image = Image.new('RGBA', size=(100, 100), color=(155, 0, 0))
        image.save(file, 'png')
        file.name = 'test.png'
        file.seek(0)

        response = self.client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            {
                "text": message_1,
                "sender_username": mask_username,
            },
            HTTP_PUBLIC_KEY=str(self.project.public_key),
            HTTP_USER_NAME=user_email_1,
            HTTP_USER_SECRET=user_password_1
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['sender_username'], mask_username)

    def test_post_chat_message_needs_text_or_attachments(self):
        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 400)

    def test_post_chat_messages_another_chat_person(self):
        temp_person = Person.objects.create(
            project=self.project, username=user_email_2, secret=user_password_2)
        ChatPerson.objects.create(chat=self.chat, person=temp_person)

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            data={"text": message_1},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)

        self.assertEqual(data['text'], message_1)
        self.assertEqual(data['sender']['username'], user_email_2)

        self.assertEqual(len(Message.objects.all()), 1)

    def test_post_chat_message_must_be_chat_person(self):
        ChatPerson.objects.all().delete()

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            data={"text": message_1},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Message.objects.all()), 0)

    def test_post_chat_messages_must_be_your_project(self):
        ChatPerson.objects.all().delete()

        temp_project = Project.objects.create(
            owner=self.user, title=project_title_2)
        Person.objects.create(project=temp_project,
                              username=user_email_2, secret=user_password_2)

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            data={"text": message_1},
            headers={
                "public-key": str(temp_project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Message.objects.all()), 0)

    def test_post_chat_message_needs_auth(self):
        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/messages/'.format(self.chat.pk),
            data={"text": message_1},
            headers={}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Message.objects.all()), 0)
