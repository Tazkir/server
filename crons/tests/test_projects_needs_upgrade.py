from datetime import datetime, timedelta
import pytz

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from accounts.models import User
from chats.models import Person
from projects.models import Project
from crons.views import ProjectsNeedsUpgrade

USER = 'alamorre@gmail.com'
PASS = 'pass1234'

PROJECT = 'Project'


class ProjectNeedsUpgradeTestCase(APITestCase):
    def setUp(self):
        self.upgrader = User.objects.create(email='upgrader@chatengine.io', password=PASS)
        self.user = User.objects.create(email=USER, password=PASS, admin=True, staff=True)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)

    def test_basic_project_needing_upgrade(self):
        for i in range(0, self.project.monthly_users + 1):
            Person.objects.create(project=self.project, username=str(i), secret=str(i))

        self.assertEqual(self.project.upgrade_reminder_date_time, None)
        self.assertEqual(len(Person.objects.all()), self.project.monthly_users + 1)

        factory = APIRequestFactory()
        view = ProjectsNeedsUpgrade.as_view()
        request = factory.get('/crons/projects_needs_upgrade/')
        force_authenticate(request, user=self.upgrader)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['emails']), 1)
        project = Project.objects.first()
        self.assertNotEqual(project.upgrade_reminder_date_time, None)

        factory = APIRequestFactory()
        view = ProjectsNeedsUpgrade.as_view()
        request = factory.get('/crons/projects_needs_upgrade/')
        force_authenticate(request, user=self.upgrader)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['emails']), 0)

        now = datetime.now().replace(tzinfo=pytz.UTC)
        self.project.upgrade_reminder_date_time = now - timedelta(weeks=2)
        self.project.save()

        factory = APIRequestFactory()
        view = ProjectsNeedsUpgrade.as_view()
        request = factory.get('/crons/projects_needs_upgrade/')
        force_authenticate(request, user=self.upgrader)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['emails']), 1)
        project = Project.objects.first()
        self.assertGreater(project.upgrade_reminder_date_time, now)

    def test_production_project_needing_upgrade(self):
        self.project.plan_type = 'production'
        self.project.save()
        self.project = Project.objects.first()

        for i in range(0, self.project.monthly_users + 1):
            Person.objects.create(project=self.project, username=str(i), secret=str(i))

        self.assertEqual(self.project.upgrade_reminder_date_time, None)
        self.assertEqual(len(Person.objects.all()), self.project.monthly_users + 1)

        factory = APIRequestFactory()
        view = ProjectsNeedsUpgrade.as_view()
        request = factory.get('/crons/projects_needs_upgrade/')
        force_authenticate(request, user=self.upgrader)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['emails']), 1)
        project = Project.objects.first()
        self.assertNotEqual(project.upgrade_reminder_date_time, None)

    def test_inactive_project(self):
        self.project.is_active = False
        self.project.save()

        factory = APIRequestFactory()
        view = ProjectsNeedsUpgrade.as_view()
        request = factory.get('/crons/projects_needs_upgrade/')
        force_authenticate(request, user=self.upgrader)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['inactive']), 1)

    def test_upgrade_not_as_upgrader(self):
        factory = APIRequestFactory()
        view = ProjectsNeedsUpgrade.as_view()
        request = factory.get('/crons/projects_needs_upgrade/')
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 400)
