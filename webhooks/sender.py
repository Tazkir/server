import requests
import urllib3

from django.http import Http404
from django.shortcuts import get_object_or_404

from .models import Webhook
from .serializers import WebhookSerializer


class Hook:
    def __init__(self):
        pass

    def post(self, event_trigger=None, project_json=None, chat_json=None, person_json=None, message_json=None, timeout=0.5):
        try:
            webhook = get_object_or_404(Webhook, project=project_json['public_key'], event_trigger=event_trigger)
            webhook_json = WebhookSerializer(webhook, many=False).data

            data = {
                "project": project_json,
                "webhook": webhook_json,
                "chat": chat_json,
                "person": person_json,
                "message": message_json
            }

            try:
                response = requests.post(webhook.url, json=data, timeout=timeout)
                return response, data

            except requests.exceptions.ReadTimeout:
                return None, data

            except urllib3.exceptions.MaxRetryError:
                return None, data

            except requests.exceptions.ConnectionError:
                return None, data

        except Http404:
            return None, None


hook = Hook()
