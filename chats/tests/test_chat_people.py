from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat, ChatPerson, Message
from projects.models import User, Project

EMAIL_1 = 'adam@gmail.com'
PASS_1 = 'potato_123'

EMAIL_2 = 'eve@gmail.com'
PASS_2 = 'pretzel_123'

EMAIL_3 = 'eve@gmail.ca'

TITLE_1 = "Chat Engine Project 1"
TITLE_2 = "Chat Engine Project 2"

CHAT_TITLE_1 = "Chat Engine Chat 1"
CHAT_TITLE_2 = "Chat Engine Chat 2"


class GetChatPeopleTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL_1, password=PASS_1)
        self.project = Project.objects.create(owner=self.user, title=TITLE_1)
        self.person = Person.objects.create(username=EMAIL_1, secret=PASS_1, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_TITLE_1)

    def test_get_chat_people(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )

        self.assertEqual(response.status_code, 200)

    def test_get_chat_people_needs_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk))
        )

        self.assertEqual(response.status_code, 403)

    def test_get_chat_people_needs_to_be_in_chat(self):
        temp_person = Person.objects.create(
            username=EMAIL_2, secret=PASS_1, project=self.project)
        temp_chat = Chat.objects.create(
            project=self.project, admin=temp_person, title=CHAT_TITLE_1)

        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(temp_chat.pk)),
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )

        self.assertEqual(response.status_code, 404)


class PostChatPeopleTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL_1, password=PASS_1)
        self.project = Project.objects.create(owner=self.user, title=TITLE_1)
        self.person = Person.objects.create(username=EMAIL_1, secret=PASS_1, project=self.project)
        self.person_2 = Person.objects.create(username=EMAIL_2, secret=PASS_2, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_TITLE_1)

    def test_post_chat_person_as_admin(self):
        self.assertEqual(len(ChatPerson.objects.all()), 1)

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            data={"username": EMAIL_2},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['person']['username'], EMAIL_2)
        self.assertEqual(len(ChatPerson.objects.all()), 2)

    def test_post_chat_person_as_member(self):
        ChatPerson.objects.create(chat=self.chat, person=self.person_2)

        Person.objects.create(project=self.project, username=EMAIL_3, secret=PASS_2)

        self.assertEqual(len(ChatPerson.objects.all()), 2)

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            data={"username": EMAIL_3},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_2,
                "user-secret": PASS_2
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['person']['username'], EMAIL_3)
        self.assertEqual(len(ChatPerson.objects.all()), 3)

    def test_post_chat_person_needs_auth(self):
        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            data={"username": EMAIL_1},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(ChatPerson.objects.all()), 1)

    def test_post_chat_person_needs_to_be_your_project(self):
        temp_project = Project.objects.create(owner=self.user, title=TITLE_1)
        temp_person = Person.objects.create(username=EMAIL_2, secret=PASS_2, project=temp_project)
        temp_chat = Chat.objects.create(project=temp_project, admin=temp_person, title=CHAT_TITLE_2)

        client = RequestsClient()
        response = client.post(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(temp_chat.pk)),
            data={"username": EMAIL_1},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(ChatPerson.objects.all()), 2)


class PatchChatPeopleTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL_1, password=PASS_1)
        self.project = Project.objects.create(owner=self.user, title=TITLE_1)
        self.person = Person.objects.create(username=EMAIL_1, secret=PASS_1, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_TITLE_1)
        self.message = Message.objects.create(chat=self.chat, sender=self.person, text='Hello world')

    def test_read_last_message(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            data={"last_read": self.message.pk},
            headers={
                "project-id": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['people'][0]['person']['username'], EMAIL_1)
        self.assertEqual(data['people'][0]['last_read'], self.message.pk)

    def test_read_message_needs_auth(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            data={"last_read": self.message.pk},
        )

        self.assertEqual(response.status_code, 403)

    def test_read_message_must_be_in_chat(self):
        temp_chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_TITLE_1)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(temp_chat.pk)),
            data={"last_read": self.message.pk},
            headers={
                "project-id": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )

        self.assertEqual(response.status_code, 404)


class DeleteChatPeopleTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL_1, password=PASS_1)
        self.project = Project.objects.create(owner=self.user, title=TITLE_1)
        self.person = Person.objects.create(username=EMAIL_1, secret=PASS_1, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_TITLE_1)

    def test_delete_chat_person(self):
        client = RequestsClient()
        response = client.put(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            data={"username": self.person.username},
            headers={
                "project-id": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['person']['username'], EMAIL_1)
        self.assertEqual(len(ChatPerson.objects.all()), 0)

    def test_delete_chat_person_needs_auth(self):
        client = RequestsClient()
        response = client.put(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            data={"username": self.person.username},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": EMAIL_1
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(ChatPerson.objects.all()), 1)

    def test_delete_chat_person_needs_to_be_your_project(self):
        temp_project = Project.objects.create(owner=self.user, title=TITLE_1)
        temp_person = Person.objects.create(username=EMAIL_2, secret=PASS_2, project=temp_project)
        temp_chat = Chat.objects.create(project=temp_project, admin=temp_person, title=CHAT_TITLE_2)

        client = RequestsClient()
        response = client.put(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(temp_chat.pk)),
            data={"title": temp_person.username},
            headers={
                "project-id": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(ChatPerson.objects.all()), 2)


class LeaveChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=EMAIL_1, password=PASS_1)
        self.project = Project.objects.create(owner=self.user, title=TITLE_1)
        self.person = Person.objects.create(username=EMAIL_1, secret=PASS_1, project=self.project)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT_TITLE_1)

    def test_leave_chat(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk)),
            headers={
                "project-id": str(self.project.public_key),
                "user-name": EMAIL_1,
                "user-secret": PASS_1
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['person']['username'], EMAIL_1)
        self.assertEqual(len(ChatPerson.objects.all()), 0)

    def test_leave_chat_needs_auth(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/chats/{}/people/'.format(str(self.chat.pk))
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(ChatPerson.objects.all()), 1)
