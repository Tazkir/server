from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from chats.models import Person

from projects.models import User, Project

from webhooks.models import Webhook
from webhooks.views import WebhookDetailsWeb


USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

TRIGGER = 'On New Message'
TRIGGER_2 = 'On Edit Chat'

URL = 'https://youtube.com'
URL_2 = 'http://youtube.ca'

PROJECT_1 = "Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'
PROJECT_2 = "Engine 2"


class GetProjectChatTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=self.project)
        self.webhook = Webhook.objects.create(project=self.project, event_trigger=TRIGGER, url=URL)

    def test_get_project_webhook_details(self):
        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.get('/projects/{}/webhooks/{}/'.format(self.project.pk, self.webhook.event_trigger))
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['url'], self.webhook.url)
        self.assertEqual(response.data['event_trigger'], self.webhook.event_trigger)

    def test_get_projects_needs_auth(self):
        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.get('/projects/{}/webhooks/{}/'.format(self.project.pk, self.webhook.event_trigger))
        response = view(request, project_id=self.project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 401)


class PatchProjectWebhookTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=self.project)
        self.webhook = Webhook.objects.create(project=self.project, event_trigger=TRIGGER, url=URL)

    def test_patch_project_webhook(self):
        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.patch(
            '/projects/{}/webhooks/{}/'.format(self.project.pk, self.webhook.event_trigger),
            json.dumps({"event_trigger": TRIGGER_2}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['url'], URL)
        self.assertEqual(response.data['event_trigger'], TRIGGER_2)

        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.patch(
            '/projects/{}/webhooks/{}/'.format(self.project.pk, self.webhook.event_trigger),
            json.dumps({"url": URL_2}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk, event_trigger=TRIGGER_2)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['url'], URL_2)
        self.assertEqual(response.data['event_trigger'], TRIGGER_2)

    def test_patch_project_webhook_needs_auth(self):
        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.patch(
            '/projects/{}/webhooks/{}/'.format(self.project.pk, self.webhook.event_trigger),
            json.dumps({"event_trigger": TRIGGER_2}),
            content_type='application/json'
        )
        response = view(request, project_id=self.project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 401)

    def test_patch_project_webhook_cannot_be_another_project(self):
        temp_user = User.objects.create(email=USER_EMAIL_2, password='123')
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)

        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.patch(
            '/projects/{}/webhooks/{}/'.format(temp_project.pk, self.webhook.event_trigger),
            json.dumps({"event_trigger": TRIGGER_2}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=temp_project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 404)


class DeleteProjectWebhookTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.person = Person.objects.create(username=USER_EMAIL, secret=USER_PASSWORD, project=self.project)
        self.webhook = Webhook.objects.create(project=self.project, event_trigger=TRIGGER, url=URL)

    def test_delete_project_webhook(self):
        self.assertEqual(len(Webhook.objects.all()), 1)

        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.delete(
            '/projects/{}/webhooks/{}/'.format(self.project.pk, self.webhook.event_trigger),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=self.project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['url'], URL)
        self.assertEqual(response.data['event_trigger'], TRIGGER)
        self.assertEqual(len(Webhook.objects.all()), 0)

    def test_delete_project_webhook_needs_auth(self):
        self.assertEqual(len(Webhook.objects.all()), 1)

        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.delete(
            '/projects/{}/webhooks/{}/'.format(self.project.pk, self.webhook.event_trigger),
            content_type='application/json'
        )
        response = view(request, project_id=self.project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(Webhook.objects.all()), 1)

    def test_delete_project_webhook_cannot_be_another_project(self):
        self.assertEqual(len(Webhook.objects.all()), 1)

        temp_user = User.objects.create(email=USER_EMAIL_2, password='123')
        temp_project = Project.objects.create(owner=temp_user, title=PROJECT_2)

        factory = APIRequestFactory()
        view = WebhookDetailsWeb.as_view()
        request = factory.delete(
            '/projects/{}/webhooks/{}/'.format(temp_project.pk, self.webhook.event_trigger),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, project_id=temp_project.pk, event_trigger=self.webhook.event_trigger)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Webhook.objects.all()), 1)
