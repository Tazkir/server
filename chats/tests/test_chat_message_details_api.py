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

chat_title_1 = "Chat Engine Chat 1"
chat_title_2 = "Chat Engine Chat 2"

message_1 = 'Hello world'
message_2 = 'Bye bye'


class GetChatMessageDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)
        self.message = Message.objects.create(chat=self.chat, sender=self.person, text=message_1)

    def test_get_chat_message(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['text'], message_1)
        self.assertEqual(data['sender']['username'], user_email_1)

    def test_get_chat_message_with_chat_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['text'], message_1)
        self.assertEqual(data['sender']['username'], user_email_1)

    def test_get_chat_message_another_chat_person(self):
        temp_person = Person.objects.create(project=self.project, username=user_email_2, secret=user_password_2)
        ChatPerson.objects.create(chat=self.chat, person=temp_person)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['text'], message_1)
        self.assertEqual(data['sender']['username'], user_email_1)

    def test_get_chat_message_must_be_chat_person(self):
        ChatPerson.objects.all().delete()

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_get_chat_message_must_be_in_this_chat(self):
        temp_person = Person.objects.create(project=self.project, username=user_email_2, secret=user_password_2)
        temp_chat = Chat.objects.create(project=self.project, title=project_title_2, admin=temp_person)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_get_chat_message_must_be_in_this_project(self):
        temp_project = Project.objects.create(owner=self.user, title=project_title_2)
        Person.objects.create(project=temp_project, username=user_email_2, secret=user_password_2)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(
                self.chat.pk, self.message.pk),
            headers={
                "public-key": str(temp_project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_get_chat_messages_needs_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            headers={}
        )

        self.assertEqual(response.status_code, 403)


class PatchChatMessageDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)
        self.message = Message.objects.create(chat=self.chat, sender=self.person, text=message_1)

    def test_patch_chat_message(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            data={"text": message_2},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['text'], message_2)
        self.assertEqual(data['sender']['username'], user_email_1)

    def test_patch_chat_message_with_chat_auth(self):
        tmp_msg = Message.objects.create(chat=self.chat, text='.')

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, tmp_msg.pk),
            data={"text": message_2},
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['text'], message_2)
        self.assertEqual(data['sender'], None)

    def test_patch_chat_message_must_be_chat_person(self):
        ChatPerson.objects.all().delete()

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(
                self.chat.pk, self.message.pk),
            data={"text": message_2},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_patch_chat_message_must_be_the_sender(self):
        temp_person = Person.objects.create(project=self.project, username=user_email_2, secret=user_password_2)
        ChatPerson.objects.create(chat=self.chat, person=temp_person)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            data={"text": message_2},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_patch_chat_message_must_be_in_this_project(self):
        temp_project = Project.objects.create(owner=self.user, title=project_title_2)
        Person.objects.create(project=temp_project, username=user_email_2, secret=user_password_2)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(
                self.chat.pk, self.message.pk),
            data={"text": message_2},
            headers={
                "public-key": str(temp_project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)

    def test_patch_chat_messages_needs_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(
                self.chat.pk, self.message.pk),
            data={"text": message_2},
            headers={}
        )

        self.assertEqual(response.status_code, 403)


class DeleteChatMessageDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(project=self.project, username=user_email_1, secret=user_password_1)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=chat_title_1)
        self.message = Message.objects.create(chat=self.chat, sender=self.person, text=message_1)

    def test_delete_chat_message(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, self.message.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Message.objects.all()), 0)

    def test_delete_chat_message_needs_chat_auth(self):
        temp_msg = Message.objects.create(chat=self.chat, text='...')
        self.assertEqual(len(Message.objects.all()), 2)

        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, temp_msg.pk),
            headers={
                "public-key": str(self.project.public_key),
                "chat-id": str(self.chat.id),
                "access-key": self.chat.access_key
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Message.objects.all()), 1)

    def test_delete_chat_message_must_be_chat_sender(self):
        temp_person = Person.objects.create(project=self.project, username='...', secret='...')
        ChatPerson.objects.create(chat=self.chat, person=temp_person)
        temp_msg = Message.objects.create(chat=self.chat, sender=temp_person, text='...')

        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(self.chat.pk, temp_msg.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_1,
                "user-secret": user_password_1
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Message.objects.all()), 2)

    def test_delete_chat_message_must_be_the_sender(self):
        temp_person = Person.objects.create(project=self.project, username=user_email_2, secret=user_password_2)
        ChatPerson.objects.create(chat=self.chat, person=temp_person)

        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(
                self.chat.pk, self.message.pk),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Message.objects.all()), 1)

    def test_delete_chat_message_must_be_in_this_project(self):
        temp_project = Project.objects.create(owner=self.user, title=project_title_2)
        Person.objects.create(project=temp_project, username=user_email_2, secret=user_password_2)

        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(
                self.chat.pk, self.message.pk),
            headers={
                "public-key": str(temp_project.public_key),
                "user-name": user_email_2,
                "user-secret": user_password_2
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Message.objects.all()), 1)

    def test_delete_chat_messages_needs_auth(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/messages/{}/'.format(
                self.chat.pk, self.message.pk),
            headers={}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Message.objects.all()), 1)
