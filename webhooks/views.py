import sendgrid

from python_http_client.exceptions import HTTPError

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.throttling import UserRateThrottle
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404

from server.settings import get_secret

from tracking.mixpanel import mix_panel

from projects.models import Project

from .models import Webhook
from .serializers import WebhookSerializer

sg = sendgrid.SendGridAPIClient(get_secret('SEND_GRID_KEY'))


class Webhooks(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        admin = request.data['chat']['admin']['username']
        sender = request.data['message']['sender_username']

        # Only adam_lamorre messages should be sent.
        if sender != admin:
            return Response({'message': 'Nothing sent'}, status=status.HTTP_200_OK)

        to_email = request.data['chat']['title']
        text = request.data['message']['text']
        link = 'https://chatengine.io'
        data = {
            "personalizations": [
                {
                    "to": [{"email": to_email}],
                    "substitutions": {"-email-": sender, "-text-": text, '-link-': link}
                }
            ],
            "from": {"email": "no_reply@chatengine.io"},
            "template_id": "0932c040-04e9-4239-8fb5-de73372c7e06"
        }

        sg.client.mail.send.post(request_body=data)

        return Response({'message': 'Passed'}, status=status.HTTP_200_OK)


class WebhookTest(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        return Response({'message': 'Passed'}, status=status.HTTP_200_OK)


class WebhooksWeb(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request, project_id):
        project = get_object_or_404(Project, owner=request.user, pk=project_id)
        webhooks = Webhook.objects.filter(project=project)
        serializer = WebhookSerializer(webhooks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, project_id):
        project = get_object_or_404(Project, owner=request.user, pk=project_id)
        serializer = WebhookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=project)
            mix_panel.track(str(request.user), 'new webhook')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebhookDetailsWeb(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request, project_id, event_trigger):
        project = get_object_or_404(Project, owner=request.user, pk=project_id)
        webhook = get_object_or_404(Webhook, project=project, event_trigger=event_trigger.replace("%20", " "))
        serializer = WebhookSerializer(webhook, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, project_id, event_trigger):
        project = get_object_or_404(Project, owner=request.user, pk=project_id)
        webhook = get_object_or_404(Webhook, project=project, event_trigger=event_trigger.replace("%20", " "))
        serializer = WebhookSerializer(webhook, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            mix_panel.track(str(request.user), 'edit webhook')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, project_id, event_trigger):
        project = get_object_or_404(Project, owner=request.user, pk=project_id)
        webhook = get_object_or_404(Webhook, project=project, event_trigger=event_trigger.replace("%20", " "))
        webhook_json = WebhookSerializer(webhook, many=False).data
        mix_panel.track(str(request.user), 'delete webhook')
        webhook.delete()
        return Response(webhook_json, status=status.HTTP_200_OK)
