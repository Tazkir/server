from rest_framework.utils import json
from rest_framework.test import APITestCase, RequestsClient

from chats.models import Person
from projects.models import User, Project

user_email_1 = 'adam@gmail.com'
user_password_1 = 'potato_123'

user_email_2 = 'eve@gmail.com'
user_password_2 = 'pretzel_123'

project_title_1 = "Chat Engine 1"

first_name = 'Adam'
last_name = 'La Morre'


class GetProjectPersonTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)

    def test_get_person(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk)),
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_1)
        self.assertNotEqual(data['secret'], user_password_1)

    def test_get_person_needs_auth(self):
        client = RequestsClient()
        response = client.get(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk)),
            headers={"private-key": '...'}
        )

        self.assertEqual(response.status_code, 403)


class PatchProjectPersonTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)

    def test_patch_person(self):
        old_password = self.person.secret

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk)),
            data={
                "username": user_email_2,
                'email': user_email_2,
                'first_name': first_name,
                'last_name': last_name
            },
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_2)
        self.assertEqual(data['email'], user_email_2)
        self.assertEqual(data['first_name'], first_name)
        self.assertEqual(data['last_name'], last_name)
        self.assertEqual(data['secret'], old_password)
        self.assertEqual(data['is_online'], False)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk)),
            data={
                "username": user_email_2,
                "secret": user_password_2,
                'email': '',
                'first_name': '',
                'last_name': '',
                "is_online": True
            },
            headers={"private-key": str(self.project.private_key)}
        )
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['username'], user_email_2)
        self.assertEqual(data['email'], '')
        self.assertEqual(data['first_name'], '')
        self.assertEqual(data['last_name'], '')
        self.assertNotEqual(data['secret'], old_password)
        self.assertNotEqual(data['secret'], user_password_2)
        self.assertEqual(data['is_online'], True)

    def test_patch_person_cannot_use_another_username(self):
        person = Person.objects.create(username='adam', secret=user_password_1, project=self.project)

        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk)),
            data={"username": person.username},
            headers={"private-key": str(self.project.private_key)}
        )

        self.assertEqual(response.status_code, 400)

    def test_patch_person_needs_auth(self):
        client = RequestsClient()
        response = client.patch(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk)),
            data={"username": user_email_2, "secret": user_password_2}
        )

        self.assertEqual(response.status_code, 403)


class DeleteProjectPersonTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=user_email_1, password=user_password_1)
        self.project = Project.objects.create(owner=self.user, title=project_title_1)
        self.person = Person.objects.create(username=user_email_1, secret=user_password_1, project=self.project)

    def test_delete_person(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk)),
            headers={"private-key": str(self.project.private_key)}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(Person.objects.all()), 0)

    def test_delete_person_needs_auth(self):
        client = RequestsClient()
        response = client.delete(
            'http://127.0.0.1:8000/projects/people/{}/'.format(str(self.person.pk))
        )

        self.assertEqual(response.status_code, 403)
