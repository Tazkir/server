from datetime import datetime, timedelta
import json
import pytz
import channels

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.throttling import AnonRateThrottle
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from chats.models import Chat, Message, ChatPerson
from projects.models import Project, Person, Collaborator

from .notifier import Emailer

emailer = Emailer()


class PurgeOldMessages(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        data = []
        now = datetime.now().replace(tzinfo=pytz.UTC)

        for chat in Chat.objects.all():
            chat_data = {}
            chat_data['message_history'] = chat.project.message_history

            for message in Message.objects.filter(chat=chat):
                if message.created < now - timedelta(days=chat.project.message_history):
                    if chat_data.get('deleted_message_stamps', False):
                        chat_data['deleted_message_stamps'].append(message.created)
                    else:
                        chat_data['deleted_message_stamps'] = [message.created]
                    message.delete()

                else:
                    if chat_data.get('good_message_stamps', False):
                        chat_data['good_message_stamps'].append(message.created)
                    else:
                        chat_data['good_message_stamps'] = [message.created]

            data.append(chat_data)

        return Response(data, status=status.HTTP_200_OK)


class ProjectsNeedsUpgrade(APIView):
    throttle_classes = [AnonRateThrottle]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request):
        if request.user.email != 'upgrader@chatengine.io':
            return Response({'message': 'wrong user...'}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            "needs_upgrade": [],
            "inactive": [],
            "emails": []
        }

        for project in Project.objects.all():
            if not project.is_active:
                data['inactive'].append(
                    '{}: {} ({}) {} users'.format(
                        str(project.owner),
                        str(project.title),
                        str(project.public_key),
                        str(project.people.count())
                    )
                )

            elif project.people.count() > project.monthly_users:
                data['needs_upgrade'].append(
                    '{}: {} ({}) {} users'.format(
                        str(project.owner),
                        str(project.title),
                        str(project.public_key),
                        str(project.people.count())
                    )
                )

                now = datetime.now().replace(tzinfo=pytz.UTC)
                week_ago = now - timedelta(weeks=1)

                if project.upgrade_reminder_date_time is None or project.upgrade_reminder_date_time < week_ago:
                    emailer.send_upgrade_note(to_email='adam@lamorre.co', project=project)
                    emailer.send_upgrade_note(to_email=project.owner.email, project=project)
                    project.upgrade_reminder_date_time = now
                    project.save()
                    data['emails'].append(project.public_key)

        return Response(data, status=status.HTTP_200_OK)


class ApplyChatUpdates(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        for chat in Chat.objects.all():
            query = Message.objects.filter(chat=chat)
            message = query.latest('created') if len(query) > 0 else None

            for chat_person in ChatPerson.objects.filter(chat=chat):
                if message is not None:
                    chat_person.chat_updated = message.created
                else:
                    chat_person.chat_updated = chat.created
                chat_person.save()

        return Response({'message': 'ok'}, status=status.HTTP_200_OK)


class SyncMemberIDs(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        data = {}
        for chat_person in ChatPerson.objects.all():
            members_ids = json.loads(chat_person.chat.members_ids)
            if chat_person.person.pk not in members_ids:
                members_ids = sorted(members_ids + [chat_person.person.pk])
            chat_person.chat.members_ids = str(members_ids)
            chat_person.chat.save()
            data[chat_person.chat.pk] = str(members_ids)
        return Response(data, status=status.HTTP_200_OK)


class PruneBusinessChat(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        project = Project.objects.get(public_key='a52241fb-be96-4763-8460-a97d46c979a2')
        count = 0
        for person in Person.objects.filter(project=project):
            if len(person.username) > 90:
                person.delete()
                count += 1
        return Response({count: count}, status=status.HTTP_200_OK)


class ReceiveBuffer(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        receive_buffer = channels.layers.channel_layers.backends['default'].receive_buffer
        return Response(
            {
                "mem": str(receive_buffer),
                "len": len(str(receive_buffer).split(',')),
            },
            status=status.HTTP_200_OK
        )


class OwnerToAdmin(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.IsAdminUser,)

    def get(self, request):
        admins = []
        for project in Project.objects.all():
            collaborator = Collaborator.objects.create(
                user=project.owner,
                project=project,
                role='admin'
            )
            admins.append(str(collaborator))

        return Response({"admins": admins}, status=status.HTTP_200_OK)


personal_email_data = [
    '@gmail.',
    '.edu',
    'mail.ru',
    'icloud.com',
    '@yahoo',
    '@hotmail',
    '@live.',
    '@outlook.',
    'mail.com',
    'example.com',
    '@protonmail.com',
    'gmial.com',
    '.ac.in',
    '@yandex',
    '@qq.com',
    '@naver.com',
]


class BusinessAccounts(APIView):
    throttle_classes = [AnonRateThrottle]
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request):
        if request.user.email != 'upgrader@chatengine.io':
            return Response({'message': 'wrong user...'}, status=status.HTTP_400_BAD_REQUEST)

        users = []
        for user in User.objects.all().order_by('-created'):
            if not any(ext in user.email for ext in personal_email_data):
                user_data = '{} - {}'.format(user.email, user.created)
                users.append(user_data)

        return Response(users, status=status.HTTP_200_OK)
