from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from chats.models import Person

from projects.models import User, Project

from webhooks.models import Webhook
from webhooks.views import WebhooksWeb

USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

TRIGGER = 'On New Message'
URL = 'https://youtube.com'

PROJECT_1 = "Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'
PROJECT_2 = "Engine 2"


class GetProjectWebhooksTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=self.project)

    def test_get_project_webhooks(self):
        Webhook.objects.create(project=self.project, event_trigger=TRIGGER, url=URL)

        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.get('/projects/{}/webhooks/'.format(self.project.pk))
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_project_webhooks_needs_auth(self):
        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.get('/projects/{}/webhooks/'.format(self.project.pk))
        response = view(request, project_id=self.project.pk)

        self.assertEqual(response.status_code, 401)

    def test_cannot_get_another_project_webhooks(self):
        temp_user = User.objects.create(email=USER_EMAIL_2, password=USER_PASSWORD)
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)

        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.get('/projects/{}/webhooks/'.format(temp_project.pk))
        force_authenticate(request, user=self.user)
        response = view(request, project_id=temp_project.pk)

        self.assertEqual(response.status_code, 404)


class PostProjectWebhookTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(project=self.project, username=USER_EMAIL)

    def test_post_project_(self):
        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.post(
            '/projects/{}/chats/'.format(self.project.pk),
            json.dumps({"url": URL, "event_trigger": TRIGGER}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['url'], URL)
        self.assertEqual(response.data['event_trigger'], TRIGGER)
        self.assertEqual(len(response.data['secret']), 40)
        self.assertEqual(len(Webhook.objects.all()), 1)

    def test_post_project_webhook_needs_event_trigger(self):
        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.post(
            '/projects/{}/chats/'.format(self.project.pk),
            json.dumps({"url": URL}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Webhook.objects.all()), 0)

    def test_post_project_webhook_needs_url(self):
        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.post(
            '/projects/{}/chats/'.format(self.project.pk),
            json.dumps({"event_trigger": TRIGGER}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Webhook.objects.all()), 0)

    def test_post_project_webhook_needs_auth(self):
        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.post(
            '/projects/{}/chats/'.format(self.project.pk),
            json.dumps({"event_trigger": TRIGGER}),
            content_type='application/json'
        )
        response = view(request, project_id=self.project.pk)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(Webhook.objects.all()), 0)

    def test_post_project_webhook_cannot_be_another_project(self):
        temp_user = User.objects.create(email=USER_EMAIL_2, password=USER_PASSWORD)
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)

        factory = APIRequestFactory()
        view = WebhooksWeb.as_view()
        request = factory.post(
            '/projects/{}/chats/'.format(temp_project.pk),
            json.dumps({"event_trigger": TRIGGER, 'url': URL}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=temp_project.pk)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Webhook.objects.all()), 0)
