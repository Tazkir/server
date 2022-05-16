from rest_framework import serializers
from rest_framework.fields import DateTimeField

from projects.serializers import PersonPublicSerializer

from .models import Chat, ChatPerson, Message, Attachment


class PersonSearchSerializer(serializers.Serializer):
    search = serializers.CharField(required=True)


class AttachmentSerializer(serializers.ModelSerializer):

    class Meta(object):
        model = Attachment
        exclude = ['chat', 'message']


class MessageSerializer(serializers.ModelSerializer):
    sender = PersonPublicSerializer(read_only=True, many=False, required=False)
    created = serializers.CharField(required=False)

    attachments = AttachmentSerializer(many=True, required=False)

    class Meta(object):
        model = Message
        exclude = ['chat']


class ChatPersonSerializer(serializers.ModelSerializer):
    person = PersonPublicSerializer(many=False, required=False)

    class Meta(object):
        model = ChatPerson
        exclude = ['id', 'chat']


class ChatSerializer(serializers.ModelSerializer):
    admin = PersonPublicSerializer(required=False)
    people = ChatPersonSerializer(many=True, required=False)
    attachments = AttachmentSerializer(many=True, required=False)
    last_message = serializers.SerializerMethodField(required=False)

    def get_last_message(self, obj):
        query = Message.objects.filter(chat=obj)
        message = query.first() if len(query) > 0 else None
        serializer = MessageSerializer(message, many=False)
        return serializer.data

    class Meta(object):
        model = Chat
        exclude = ['project', 'members_ids']


class ChatActiveSinceSerializer(serializers.Serializer):
    before = DateTimeField(required=True)
