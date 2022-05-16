from rest_framework.test import APITestCase

from datetime import datetime, timedelta

import pytz

from chats.notifiers import Emailer

from chats.models import Person, Chat, Message
from projects.models import User, Project

USER = 'adam@lamorre.co'
USER_2 = 'alamorre@gmail.com'
PASSWORD = 'potato_123'

PROJECT = "Chat Engine"
CHAT = "Chat Engine"

TEXT = 'test email form pro project'

emailer = Emailer()


class EmailerTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)
        self.project = Project.objects.create(owner=self.user, title=PROJECT, email_sender='test@chatengine.io')
        self.person = Person.objects.create(project=self.project, username=USER, secret=PASSWORD, email=USER)
        self.person_2 = Person.objects.create(project=self.project, username=USER_2, secret=PASSWORD, email=USER)
        self.chat = Chat.objects.create(project=self.project, admin=self.person, title=CHAT)
        self.message = Message.objects.create(sender=self.person, chat=self.chat, text=TEXT)

    def test_notifier_emails_is_not_enabled(self):
        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'Emails disabled')

    def test_notifier_basic_plan_is_throttled(self):
        self.project.is_emails_enabled = True
        self.project.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'Free throttled')

    def test_notifier_pro_plan_no_people(self):
        self.project.plan_type = 'professional'
        self.project.is_emails_enabled = True
        self.project.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'No users qualify')

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'No users qualify')

    def test_notifier_pro_plan_online_people(self):
        self.project.plan_type = 'professional'
        self.project.is_emails_enabled = True
        self.project.save()

        self.person_2.is_online = True
        self.person_2.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person_2, self.person]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'No users qualify')

    def test_notifier_pro_plan_no_emails(self):
        self.project.plan_type = 'professional'
        self.project.is_emails_enabled = True
        self.project.save()

        self.person_2.email = ''
        self.person_2.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person_2, self.person]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'No users qualify')

        self.person_2.email = ''
        self.person_2.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person_2, self.person]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'No users qualify')

    def test_notifier_pro_plan_works(self):
        self.project.plan_type = 'professional'
        self.project.is_emails_enabled = True
        self.project.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person_2, self.person]
        )

        self.assertEqual(len(sent_list), 1)
        self.assertEqual(response, 'Success')

        self.message.text = 'Second message!!!'
        self.message.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person_2, self.person]
        )

        self.assertEqual(len(sent_list), 1)
        self.assertEqual(response, 'Success')

    def test_notifier_basic_plan_works_with_throttle(self):
        self.project.email_last_sent = self.project.email_last_sent - timedelta(minutes=6)
        self.project.email_company_name = 'Example Basic Co.'
        self.project.is_emails_enabled = True
        self.project.save()

        now = datetime.now().replace(tzinfo=pytz.UTC)

        # Email last sent is old
        self.assertTrue(self.project.email_last_sent < now)

        self.message.text = 'test email form basic project'
        self.message.save()

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person_2, self.person]
        )

        self.assertEqual(len(sent_list), 1)
        self.assertEqual(response, 'Success')

        # Email last sent updated
        self.assertTrue(now < self.project.email_last_sent)

        response, sent_list = emailer.email_chat_members(
            project=self.project,
            message=self.message,
            people=[self.person_2, self.person]
        )

        self.assertEqual(len(sent_list), 0)
        self.assertEqual(response, 'Free throttled')
