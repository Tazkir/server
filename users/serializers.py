from rest_framework import serializers

from .models import Session


class SessionSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Session
        fields = ['token', 'expiry']
