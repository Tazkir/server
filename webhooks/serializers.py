from rest_framework import serializers

from .models import Webhook


class WebhookSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Webhook
        exclude = ['project']
