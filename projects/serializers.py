from rest_framework import serializers

from .models import Collaborator, Project, Person, Invite

from chats.models import Message, Attachment


class PersonPublicSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Person
        fields = [
            'username',
            'first_name',
            'last_name',
            'avatar',
            'custom_json',
            'is_online',
        ]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta(object):
        model = Attachment
        exclude = ['chat', 'message']


class LastMessageSerializer(serializers.ModelSerializer):
    text = serializers.CharField(required=False)
    created = serializers.CharField(required=False)
    attachments = AttachmentSerializer(many=True, required=False)

    class Meta(object):
        model = Message
        fields = ['id', 'text', 'created', 'attachments']


class CollaboratorSerializer(serializers.ModelSerializer):
    user = serializers.CharField(required=False, read_only=True)
    role = serializers.CharField(required=False)

    class Meta(object):
        model = Collaborator
        exclude = ['project']


class InviteSerializer(serializers.ModelSerializer):
    to_email = serializers.CharField(required=True)
    role = serializers.CharField(required=True)
    access_key = serializers.CharField(required=False)

    class Meta(object):
        model = Invite
        exclude = ['project']


class PersonSerializer(serializers.ModelSerializer):
    # Secret can be rendered because only the project owner uses this serializer
    is_authenticated = serializers.BooleanField(required=False, read_only=True)
    last_message = serializers.SerializerMethodField(required=False)

    def get_last_message(self, obj):
        query = Message.objects.filter(sender=obj)
        message = query.first() if len(query) > 0 else None
        serializer = LastMessageSerializer(message, many=False)
        return serializer.data

    class Meta(object):
        model = Person
        exclude = ['project']


class ProjectSerializer(serializers.ModelSerializer):
    title = serializers.CharField(required=True)
    goal = serializers.CharField(required=True)
    owner = serializers.CharField(required=False)
    plan_type = serializers.CharField(required=False)
    public_key = serializers.CharField(required=False)
    is_active = serializers.BooleanField(required=False, read_only=True)

    is_emails_enabled = serializers.BooleanField(required=False)
    email_link = serializers.URLField(required=False)
    email_sender = serializers.EmailField(required=False)
    email_last_sent = serializers.DateTimeField(required=False)
    email_company_name = serializers.CharField(required=False)

    count_chats = serializers.SerializerMethodField()
    count_people = serializers.SerializerMethodField()

    monthly_users = serializers.IntegerField(required=False)

    def get_count_chats(self, obj):
        return obj.chats.count()

    def get_count_people(self, obj):
        return obj.people.count()

    class Meta(object):
        model = Project
        fields = [
            'owner',
            'is_active',
            'public_key',
            'plan_type',
            'monthly_payment',
            'title',
            'goal',
            'created',
            # Email Notification Settings
            'is_emails_enabled',
            'email_link',
            'email_sender',
            'email_last_sent',
            'email_company_name',
            # Count Chats and Users
            'count_chats',
            'count_people',
            # Plan Limits
            'monthly_users',
        ]
