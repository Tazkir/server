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

    def send_upgrade_note(self, to_email: str, project: Project):
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "subject": "Good Job with Chat Engine 👏",
                    "substitutions": {
                        "-project_id-": str(project.pk),
                        "-project_title-": project.title,
                        "-project_plan-": project.plan_type,
                    }
                }
            ],
            "from": {"email": 'adam@lamorre.co'},
            "template_id": "8543263a-3792-414c-a4b5-faf12582afcd"
        }

        try:
            sg.client.mail.send.post(request_body=data)
            return True

        except HTTPError:
            return False
