from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat, ChatPerson
from projects.models import User, Project

USER = 'adam@gmail.com'
USER_2 = 'adam2@gmail.com'
PASSWORD = 'potato_123'
PROJECT = "Chat Engine Project"
CHAT = "Chat Engine Chat"


class GetChatsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER, secret=PASSWORD)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)
        self.client = RequestsClient()

    def test_get_chats(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data[0]['title'], CHAT)

    def test_get_chats_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/',
            headers={}
        )

        self.assertEqual(response.status_code, 403)

    def test_get_chats_needs_to_be_a_chat_person(self):
        Person.objects.create(project=self.project, username=USER_2, secret=PASSWORD)

        response = self.client.get(
            'http://127.0.0.1:8000/chats/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER_2,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(len(data), 0)
        self.assertEqual(response.status_code, 200)

    def test_get_project_people_with_params(self):
        response = self.client.get(
            'http://127.0.0.1:8000/chats/?page=1',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        response = self.client.get(
            'http://127.0.0.1:8000/chats/?page=0&page_size=0',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 0)

        Chat.objects.create(project=self.project, admin=self.person, title='...1')
        Chat.objects.create(project=self.project, admin=self.person, title='...2')

        response = self.client.get(
            'http://127.0.0.1:8000/chats/?page=0&page_size=2',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(data), 2)


class PostChatsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER, secret=PASSWORD)
        self.client = RequestsClient()

    def test_post_chat(self):
        response = self.client.post(
            'http://127.0.0.1:8000/chats/',
            data={
                "title": CHAT,
                "custom_json": json.dumps({"this": "that"})
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Chat.objects.all()), 1)
        self.assertEqual(data['admin']['username'], USER)
        self.assertEqual(json.loads(data['custom_json'])['this'], "that")
        self.assertEqual(data['title'], CHAT)

    def test_post_chat_needs_auth(self):
        response = self.client.post(
            'http://127.0.0.1:8000/chats/',
            data={"title": CHAT},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": '...'
            }
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(len(Chat.objects.all()), 0)

    def test_post_chat_title_not_required(self):
        response = self.client.post(
            'http://127.0.0.1:8000/chats/',
            data={},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Chat.objects.all()), 1)
        self.assertEqual(data['admin']['username'], USER)
        self.assertEqual(data['title'], None)


class PutChatsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER, secret=PASSWORD)
        self.person_2 = Person.objects.create(project=self.project, username=USER_2, secret=PASSWORD)
        self.client = RequestsClient()

    def test_get_or_create_chat_creates(self):
        self.assertEqual(len(Chat.objects.all()), 0)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={
                "usernames": [USER_2],
                "is_direct_chat": True
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )

        self.assertEqual(response.status_code, 201)

        data = json.loads(response.content)
        self.assertEqual(data['is_direct_chat'], True)

    def test_get_or_create_chat_gets(self):
        chat = Chat.objects.create(admin=self.person, project=self.project)
        ChatPerson.objects.create(chat=chat, person=self.person_2)

        self.assertEqual(len(Chat.objects.all()), 1)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={"usernames": [USER_2]},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_get_or_create_chat_big_list_twice(self):
        username_1 = 'abc1'
        username_2 = 'abc2'
        username_3 = 'abc3'
        username_4 = 'abc4'

        Person.objects.create(project=self.project, username=username_1, secret=PASSWORD)
        Person.objects.create(project=self.project, username=username_2, secret=PASSWORD)
        Person.objects.create(project=self.project, username=username_3, secret=PASSWORD)
        Person.objects.create(project=self.project, username=username_4, secret=PASSWORD)

        self.assertEqual(len(Chat.objects.all()), 0)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={
                "usernames": [username_1, username_3, username_2, username_4],
                "title": CHAT
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Chat.objects.all()), 1)

        data = json.loads(response.content)
        self.assertEqual(data['title'], CHAT)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={"usernames": [username_3, username_1, username_4, username_2]},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Chat.objects.all()), 1)

    def test_get_or_create_chat_needs_auth(self):
        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={"usernames": [USER_2]}
        )

        self.assertEqual(response.status_code, 403)

    def test_get_or_create_chat_one_invalid_username(self):
        self.assertEqual(len(Chat.objects.all()), 0)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={"usernames": [USER_2, '...']},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Chat.objects.all()), 0)

    def test_get_or_create_chat_after_delete_chat_person(self):
        chat = Chat.objects.create(admin=self.person, project=self.project)
        chat_person = ChatPerson.objects.create(chat=chat, person=self.person_2)

        self.assertEqual(len(Chat.objects.all()), 1)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={"usernames": [USER_2]},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Chat.objects.all()), 1)

        chat_person.delete()

        chat = Chat.objects.filter(project=self.project)[0]

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={"usernames": [USER_2]},
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Chat.objects.all()), 2)

    def test_get_or_create_chat_create_second_chat_due_to_title(self):
        self.assertEqual(len(Chat.objects.all()), 0)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={
                "usernames": [USER_2],
                "is_direct_chat": True
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['is_direct_chat'], True)
        self.assertEqual(data['title'], None)
        self.assertEqual(len(Chat.objects.all()), 1)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={
                "usernames": [USER_2],
                "is_direct_chat": True,
                "title": CHAT,
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['is_direct_chat'], True)
        self.assertEqual(data['title'], CHAT)
        self.assertEqual(len(Chat.objects.all()), 2)

        response = self.client.put(
            'http://127.0.0.1:8000/chats/',
            data={
                "usernames": [USER_2],
                "title": CHAT,
            },
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['is_direct_chat'], True)
        self.assertEqual(data['title'], CHAT)
        self.assertEqual(len(Chat.objects.all()), 2)
