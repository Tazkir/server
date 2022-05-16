from rest_framework import serializers

from .models import Feedback

from accounts.serializers import UserPublicSerializer


class FeedbackSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True, many=False, required=False)
    created = serializers.DateTimeField(required=False)
    text = serializers.CharField(required=True)

    class Meta(object):
        model = Feedback
        fields = '__all__'
