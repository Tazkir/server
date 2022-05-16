from datetime import datetime, timedelta
import pytz
import time

from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person, Chat
from projects.models import User, Project
from users.models import Session

USER = 'adam@gmail.com'
USER_2 = 'eve@gmail.com'
PASSWORD = 'potato_123'

PROJECT = "Chat Engine Project 1"
CHAT = "Chat Engine Chat 1"


class GetMyDetailsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)
        self.person = Person.objects.create(project=self.project, username=USER, secret=PASSWORD)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)
        self.client = RequestsClient()

    def test_get_or_create_session_by_create(self):
        self.assertEqual(len(Session.objects.all()), 0)
        response = self.client.get(
            'http://127.0.0.1:8000/users/me/session/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(data['token'], None)
        self.assertNotEqual(data['expiry'], None)
        self.assertEqual(len(Session.objects.all()), 1)

    def test_get_or_create_session_by_get(self):
        Session.objects.create(person=self.person)
        self.assertEqual(len(Session.objects.all()), 1)
        response = self.client.get(
            'http://127.0.0.1:8000/users/me/session/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(data['token'], None)
        self.assertNotEqual(data['expiry'], None)
        self.assertEqual(len(Session.objects.all()), 1)

    def test_get_or_create_session_refresh(self):
        now = datetime.now().replace(tzinfo=pytz.UTC)
        session = Session.objects.create(person=self.person)
        token = session.token
        session.expiry = now + timedelta(seconds=1)
        session.save()
        self.assertEqual(len(Session.objects.all()), 1)
        time.sleep(2)
        response = self.client.get(
            'http://127.0.0.1:8000/users/me/session/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER,
                "user-secret": PASSWORD
            }
        )
        data = json.loads(response.content)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(data['token'], token)
        self.assertNotEqual(data['expiry'], session.expiry)
        self.assertEqual(len(Session.objects.all()), 1)

    def test_get_or_create_session_needs_auth(self):
        response = self.client.get(
            'http://127.0.0.1:8000/users/me/session/',
            headers={
                "public-key": str(self.project.public_key),
                "user-name": USER
            }
        )
        self.assertEqual(response.status_code, 403)
