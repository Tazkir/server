from python_http_client.exceptions import HTTPError

import sendgrid

from accounts.models import User, Reset
from server.settings import get_secret

sg = sendgrid.SendGridAPIClient(get_secret('SEND_GRID_KEY'))


class Emailer():
    def __init__(self):
        pass

    def email_reset_link(self, user: User, reset: Reset):
        link = 'https://chatengine.io/reset/{}'.format(str(reset.uuid)) \
            if get_secret('PIPELINE') == 'production' else \
            'http://localhost:3000/reset/{}'.format(str(reset.uuid))

        data = {
            "personalizations": [
                {
                    "to": [{"email": user.email}],
                    "subject": "Reset Password | Chat Engine",
                    "substitutions": {
                        "-link-": link
                    }
                }
            ],
            "from": {"email": 'no_reply@chatengine.io'},
            "template_id": "02e2e343-03b3-4bee-a6b1-3e7527a3b207"
        }

        try:
            sg.client.mail.send.post(request_body=data)
            return True

        except HTTPError:
            return False

    def email_demo_requested(self, email: str, company: str, userbase: str, goals: str):
        data = {
            "personalizations": [
                {
                    "to": [{"email": email}, {"email": 'adam@lamorre.co'}],
                    "subject": "Demo Requested | Chat Engine",
                    "substitutions": {
                        "-email-": email,
                        "-company-": company,
                        "-userbase-": userbase,
                        "-goals-": goals,
                    }
                }
            ],
            "from": {"email": 'no_reply@chatengine.io'},
            "template_id": "67689bef-d9eb-4a7e-a53d-548bb4fb61e5"
        }

        try:
            sg.client.mail.send.post(request_body=data)
            return True

        except HTTPError:
            return False
