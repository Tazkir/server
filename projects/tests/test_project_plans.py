from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from projects.models import User, Project, Person
from projects.views import Projects

from chats.models import Chat

USER = 'adam@gmail.com'
PASSWORD = 'potato_123'

PROJECT = "Chat Engine 1"


class ApplyPlanProjectTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT)

    def test_project_default_plan(self):
        self.assertEqual(self.project.monthly_users, 25)
        self.assertEqual(self.project.monthly_payment, 0)
        self.assertEqual(self.project.message_history, 14)

    def test_project_modify_plan(self):
        self.project.monthly_users = 1000
        self.project.monthly_payment = 1
        self.project.message_history = 21
        self.project.save()

        self.assertEqual(self.project.monthly_users, 1000)
        self.assertEqual(self.project.monthly_payment, 1)
        self.assertEqual(self.project.message_history, 21)

    def test_project_apply_plans(self):
        self.project.monthly_users = 500
        self.project.plan_type = 'light'
        self.project.apply_plan = True
        self.project.save()

        self.assertEqual(self.project.apply_plan, False)
        self.assertEqual(self.project.monthly_users, 500)
        self.assertEqual(self.project.monthly_payment, 7)
        self.assertEqual(self.project.message_history, 30)

        self.project.plan_type = 'production'
        self.project.apply_plan = True
        self.project.save()

        self.assertEqual(self.project.apply_plan, False)
        self.assertEqual(self.project.monthly_users, 500)
        self.assertEqual(self.project.monthly_payment, 25)
        self.assertEqual(self.project.message_history, 365 * 1)

        self.project.plan_type = 'professional'
        self.project.apply_plan = True
        self.project.save()

        self.assertEqual(self.project.apply_plan, False)
        self.assertEqual(self.project.monthly_users, 500)
        self.assertEqual(self.project.monthly_payment, 36)
        self.assertEqual(self.project.message_history, 365 * 2)
