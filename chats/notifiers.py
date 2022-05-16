from datetime import datetime, timedelta

from python_http_client.exceptions import HTTPError

import pytz
import sendgrid

from chats.models import Message
from projects.models import Project, Person
from server.settings import get_secret

sg = sendgrid.SendGridAPIClient(get_secret('SEND_GRID_KEY'))
FREE_MESSAGE = 'Given your project plan, \
    no emails notifications will be sent for the next five minutes.'


class Emailer():
    def __init__(self):
        pass

    def needs_throttle(self, project_plan):
        return any(plan in project_plan for plan in ['basic', 'light'])

    def send_email(self, project: Project, message: Message, to_email: str):
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": "New Message | {}".format(
                        project.email_company_name if project.email_company_name else 'Chat Engine'
                    ),
                    "substitutions": {
                        "-email-": message.sender_username,
                        "-text-": message.text,
                        "-link-": project.email_link,
                        "-free_message-": FREE_MESSAGE if self.needs_throttle(project.plan_type) else ''
                    }
                }
            ],
            "from": {"email": project.email_sender},
            "template_id": "bf26cfb3-0460-4c03-a83a-52238cd4c5f1"
        }

        try:
            sg.client.mail.send.post(request_body=data)
            return True

        except HTTPError:
            return False

    def email_chat_members(self, project: Project, message: Message, people):
        # Make sure emails are on
        if not project.is_emails_enabled:
            return 'Emails disabled', []

        # Make sure throttle is gone
        now = datetime.now().replace(tzinfo=pytz.UTC)
        if self.needs_throttle(project.plan_type) and now < project.email_last_sent + timedelta(minutes=5):
            return 'Free throttled', []

        # Email every offline message receiver with an email
        sent_list = []
        for person in people:
            if not person.is_online and person is not message.sender and person.email:
                if self.send_email(project=project, message=message, to_email=person.email):
                    sent_list.append(person.email)

        # Make sure users send
        if len(sent_list) == 0:
            return 'No users qualify', sent_list

        # Reset throttle
        project.email_last_sent = now
        project.save()

        return 'Success', sent_list
