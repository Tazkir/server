import uuid
import json
import pytz

from jsonfield import JSONField

from datetime import datetime

from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_delete

from projects.models import Project, Person

from webhooks.sender import hook

from html_sanitizer import Sanitizer

sanitizer = Sanitizer({
    "tags": {
        "a", "h1", "h2", "h3", "strong", "em", "p", "ul", "ol", "li", "br", "sub", "sup", "hr", "code", "u"
    },
})


class Chat(models.Model):
    admin = models.ForeignKey(Person, related_name="your_chats", on_delete=models.CASCADE, blank=True, null=True)
    project = models.ForeignKey(Project, db_column="public_key", related_name="chats", on_delete=models.CASCADE)

    title = models.CharField(max_length=999, blank=True, null=True)
    is_direct_chat = models.BooleanField(default=False, blank=True, null=True)
    custom_json = JSONField(default=dict)

    members_ids = models.CharField(default='[]', max_length=999, editable=False)
    access_key = models.CharField(default="", max_length=999, editable=False)
    is_authenticated = models.BooleanField(default=True, editable=False)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return "{} - {}".format(self.project.title, self.title)

    class Meta:
        unique_together = (("project", "id"),)
        ordering = ('project', '-id')
        indexes = [
            models.Index(fields=["project", "-id"]),
            models.Index(fields=["project", "members_ids"]),
        ]


class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE, default=None, blank=True, null=True)
    sender = models.ForeignKey(Person, related_name='messages', on_delete=models.SET_NULL, default=None, blank=True, null=True)

    sender_username = models.CharField(max_length=1000, default=None, blank=True, null=True)
    # sender#_avatar_url = models.ImageField(upload_to='sender_temp_avatars', max_length=None, blank=True, null=True)

    text = models.TextField(blank=True, null=True)
    custom_json = JSONField(default=dict)

    created = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    def __str__(self):
        return "{} {}".format(self.chat, self.created)

    class Meta:
        unique_together = (("chat", "id"),)
        ordering = ["chat", "-id"]
        indexes = [
            models.Index(fields=["chat", "-id"]),
        ]

    def save(self, *args, **kwargs):
        if self.text:
            self.text = sanitizer.sanitize(self.text)
        if self.sender_username is None and self.sender is not None:
            self.sender_username = self.sender.username
        if self.created == None:
            self.created = datetime.now().replace(tzinfo=pytz.UTC)
        super(Message, self).save(*args, **kwargs)


class ChatPerson(models.Model):
    chat = models.ForeignKey(Chat, related_name='people', on_delete=models.CASCADE)
    person = models.ForeignKey(Person, related_name='chats', on_delete=models.CASCADE)

    last_read = models.ForeignKey(Message, related_name='last_reads', null=True, blank=True, on_delete=models.SET_NULL)

    chat_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "{} - {}".format(self.chat.title, self.person.username)

    class Meta:
        unique_together = (("chat", "person"),)
        ordering = ['chat', 'person']
        indexes = [
            models.Index(fields=["chat", "person"]),
            models.Index(fields=["person", "-chat_updated"]),
        ]


class Attachment(models.Model):
    chat = models.ForeignKey(Chat, related_name='attachments', on_delete=models.CASCADE)
    message = models.ForeignKey(Message, related_name='attachments', on_delete=models.CASCADE)

    file = models.FileField(upload_to='attachments', max_length=5000, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.file)

    class Meta:
        ordering = ['chat', '-created']


@receiver(post_save, sender=Chat)
def post_save_chat(instance, created, **kwargs):
    if created:
        instance.access_key = "ca-{}".format(uuid.uuid4())
        instance.save()
        ChatPerson.objects.get_or_create(chat=instance, person=instance.admin)

    from .serializers import ChatSerializer
    from projects.serializers import ProjectSerializer
    chat_json = ChatSerializer(instance, many=False).data
    project_json = ProjectSerializer(instance.project, many=False).data
    if created:
        hook.post(event_trigger='On New Chat', project_json=project_json, chat_json=chat_json)
    else:
        hook.post(event_trigger='On Edit Chat', project_json=project_json, chat_json=chat_json)


@receiver(pre_delete, sender=Chat)
def pre_delete_chat(instance, **kwargs):
    from .serializers import ChatSerializer
    from projects.serializers import ProjectSerializer
    chat_json = ChatSerializer(instance, many=False).data
    project_json = ProjectSerializer(instance.project, many=False).data
    hook.post(event_trigger='On Delete Chat', project_json=project_json, chat_json=chat_json)


@receiver(post_save, sender=Message)
def post_save_message(instance, created, **kwargs):
    from .serializers import MessageSerializer, ChatSerializer
    from projects.serializers import ProjectSerializer
    message_json = MessageSerializer(instance, many=False).data
    chat_json = ChatSerializer(instance.chat, many=False).data
    project_json = ProjectSerializer(instance.chat.project, many=False).data
    if created:
        hook.post(event_trigger='On New Message', project_json=project_json, message_json=message_json, chat_json=chat_json)
    else:
        hook.post(event_trigger='On Edit Message', project_json=project_json, message_json=message_json, chat_json=chat_json)


@receiver(pre_delete, sender=Message)
def pre_delete_message(instance, **kwargs):
    from .serializers import MessageSerializer, ChatSerializer
    from projects.serializers import ProjectSerializer
    message_json = MessageSerializer(instance, many=False).data
    chat_json = ChatSerializer(instance.chat, many=False).data
    project_json = ProjectSerializer(instance.chat.project, many=False).data
    hook.post(event_trigger='On Delete Message', project_json=project_json, message_json=message_json, chat_json=chat_json)


@receiver(post_save, sender=ChatPerson)
def post_save_chat_person(instance, created, **kwargs):
    if created:
        members_ids = json.loads(instance.chat.members_ids)
        if instance.person.pk not in members_ids:
            members_ids = sorted(members_ids + [instance.person.pk])
        instance.chat.members_ids = str(members_ids)
        instance.chat.save()
        instance.save()


@receiver(post_delete, sender=ChatPerson)
def post_delete_chat_person(instance, **kwargs):
    try:
        members_ids = json.loads(instance.chat.members_ids)
        if instance.person.pk in members_ids:
            members_ids.remove(instance.person.pk)
        instance.chat.members_ids = str(members_ids)
        instance.chat.save()

    except Chat.DoesNotExist:
        pass
