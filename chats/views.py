import os

from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlretrieve, urlcleanup

from django.core.files import File
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404

from users.publishers import chat_publisher
from users.authentication import UserSecretAuthentication

from projects.models import Person
from projects.serializers import PersonPublicSerializer

from tracking.mixpanel import mix_panel

from .notifiers import Emailer
from .authentication import ChatAccessKeyAuthentication
from .models import Chat, ChatPerson, Message, Attachment
from .serializers import ChatSerializer, MessageSerializer, ChatPersonSerializer, ChatActiveSinceSerializer, PersonSearchSerializer

emailer = Emailer()


class Chats(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication,)

    def get_param(self, request, param, default: int = 0):
        try:
            return int(request.GET.get(param, default))
        except TypeError:
            return 0

    def get(self, request):
        page = self.get_param(request=request, param='page', default=0)
        page_size = self.get_param(request=request, param='page_size', default=250)
        start = page * page_size
        end = (page * page_size) + page_size
        chat_people = ChatPerson.objects.filter(person=request.user).order_by('-chat_updated')[start:end]
        chats = [chat_person.chat for chat_person in chat_people]
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ChatSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(project=request.auth, admin=request.user)
            mix_panel.track(str(request.user), 'new chat api')
            chat_publisher.publish_chat_data('new_chat', serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        if isinstance(request.data, QueryDict):
            usernames = request.data.getlist('usernames', [])
        else:
            usernames = request.data.get('usernames', [])
        usernames = list(filter(None.__ne__, usernames))

        if request.user.username not in usernames:
            # TODO: Unsanitized input throws errors. Try a string Array serializer.
            usernames = sorted(usernames + [request.user.username])

        try:
            people = [get_object_or_404(Person, project=request.auth.pk, username=username) for username in usernames]
        except:
            return Response({"message": "At least one username is not a user"}, status=status.HTTP_400_BAD_REQUEST)

        people_ids = sorted([person.id for person in people])

        if request.data.get('title', False):
            chats = Chat.objects.filter(project=request.auth, members_ids=str(people_ids), title=request.data['title'])[:1]
        else:
            chats = Chat.objects.filter(project=request.auth, members_ids=str(people_ids))[:1]
        chat = next(iter(chats), None)

        if chat is None:
            chat = Chat.objects.create(project=request.auth, members_ids=str(people_ids), admin=request.user)
            for person in people:
                ChatPerson.objects.get_or_create(chat=chat, person=person)

            serializer = ChatSerializer(chat, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()

            mix_panel.track(str(request.user), 'new chat api')
            chat_publisher.publish_chat_data('new_chat', serializer.data)
            return Response(ChatSerializer(chat, many=False).data, status.HTTP_201_CREATED)

        return Response(ChatSerializer(chat, many=False).data, status.HTTP_200_OK)


class LatestChats(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication,)

    def get(self, request, count):
        chat_people = ChatPerson.objects.filter(person=request.user).order_by('-chat_updated')[:int(count)]
        chats = [chat_person.chat for chat_person in chat_people]
        serializer = ChatSerializer(chats, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, count):
        serializer = ChatActiveSinceSerializer(data=request.data)
        if serializer.is_valid():
            chat_people = ChatPerson.objects.filter(
                person=request.user,
                chat_updated__lt=serializer.data['before']
            ).order_by('-chat_updated')[:int(count)]
            chats = [chat_person.chat for chat_person in chat_people]
            serializer = ChatSerializer(chats, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatDetails(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication, ChatAccessKeyAuthentication,)

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth.pk, pk=chat_id)
        serializer = ChatSerializer(chat, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, chat_id):
        chat = get_object_or_404(Chat, pk=chat_id, project=request.auth)
        serializer = ChatSerializer(chat, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            mix_panel.track(str(request.user), 'edit chat')
            chat_publisher.publish_chat_data('edit_chat', serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, chat_id):
        if isinstance(request.user, Chat):
            return Response({"message": "You don't have permission"}, status=status.HTTP_403_FORBIDDEN)
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id, admin=request.user)
        chat_json = ChatSerializer(chat, many=False).data
        mix_panel.track(str(request.user), 'delete chat')
        chat_publisher.publish_chat_data('delete_chat', chat_json)
        chat.delete()  # Delete after publish!
        return Response(chat_json, status=status.HTTP_200_OK)


class ChatTyping(APIView):
    throttle_scope = 'typing'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication,)

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, pk=chat_id, project=request.auth)
        get_object_or_404(ChatPerson, chat=chat, person=request.user)
        typing_data = {'id': chat.pk, 'person': request.user.username}
        chat_publisher.publish_chat_data('is_typing', typing_data)
        return Response(typing_data, status=status.HTTP_200_OK)


class ChatPersonList(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication,)

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id)
        get_object_or_404(ChatPerson, chat=chat, person=request.user)
        chat_people = ChatPerson.objects.filter(chat=chat)
        serializer = ChatPersonSerializer(chat_people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id)
        get_object_or_404(ChatPerson, chat=chat, person=request.user)
        person = get_object_or_404(Person, project=request.auth, username=request.data.get('username'))

        chat_person, created = ChatPerson.objects.get_or_create(chat=chat, person=person)

        serializer = ChatSerializer(chat, many=False)
        mix_panel.track(str(request.user), 'add person')
        chat_publisher.publish_chat_data('add_person', serializer.data)

        if created:
            chat_publisher.publish_chat_data('new_chat', serializer.data, [person.pk])

        serializer = ChatPersonSerializer(chat_person, many=False)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def patch(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id)
        chat_person = get_object_or_404(ChatPerson, chat=chat, person=request.user)
        last_read = get_object_or_404(Message, chat=chat, id=request.data.get('last_read', None))

        serializer = ChatPersonSerializer(chat_person, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if last_read is not chat_person.last_read:
                chat_serializer = ChatSerializer(chat, many=False)
                chat_publisher.publish_chat_data('edit_chat', chat_serializer.data)
            return Response(chat_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id, admin=request.user)
        person = get_object_or_404(Person, project=request.auth, username=request.data.get('username'))
        chat_person = get_object_or_404(ChatPerson, chat=chat, person=person)
        chat_person_json = ChatPersonSerializer(chat_person, many=False).data
        chat_person.delete()  # Delete before Socket publish!
        serializer = ChatSerializer(chat, many=False)
        mix_panel.track(str(request.user), 'remove person')
        chat_publisher.publish_chat_data('remove_person', serializer.data)
        chat_publisher.publish_chat_data('delete_chat', serializer.data, [person.pk])
        return Response(chat_person_json, status=status.HTTP_200_OK)

    def delete(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id)
        chat_person = get_object_or_404(ChatPerson, chat=chat, person=request.user)
        chat_person_json = ChatPersonSerializer(chat_person, many=False).data
        chat_person.delete()  # Delete before Socket publish!
        serializer = ChatSerializer(chat, many=False)
        mix_panel.track(str(request.user), 'remove person')
        chat_publisher.publish_chat_data('remove_person', serializer.data)
        chat_publisher.publish_chat_data('delete_chat', serializer.data, [request.user.pk])
        return Response(chat_person_json, status=status.HTTP_200_OK)


class OtherChatPersonList(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication,)

    def get(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id)
        get_object_or_404(ChatPerson, person=request.user, chat=chat)
        chat_people = ChatPerson.objects.filter(chat=chat)
        chat_people_names = [chat_person.person.username for chat_person in chat_people]
        people = Person.objects.filter(project=request.auth).exclude(username__in=chat_people_names)
        serializer = PersonPublicSerializer(people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, chat_id):
        chat = get_object_or_404(Chat, project=request.auth, pk=chat_id)
        get_object_or_404(ChatPerson, person=request.user, chat=chat)
        chat_people = ChatPerson.objects.filter(chat=chat)
        chat_people_names = [chat_person.person.username for chat_person in chat_people]
        serializer = PersonSearchSerializer(data=request.data)
        if serializer.is_valid():
            username_people = Person.objects.filter(
                project=request.auth,
                username__contains=serializer.data['search']
            ).exclude(username__in=chat_people_names)[0:3]
            first_name_people = Person.objects.filter(
                project=request.auth,
                first_name__contains=serializer.data['search']
            ).exclude(username__in=chat_people_names)[0:3]
            last_name_people = Person.objects.filter(
                project=request.auth,
                last_name__contains=serializer.data['search']
            ).exclude(username__in=chat_people_names)[0:3]
            people = list(set(username_people) | set(first_name_people) | set(last_name_people))
            serializer = PersonPublicSerializer(people, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class Messages(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication, ChatAccessKeyAuthentication,)

    def get(self, request, chat_id):
        if isinstance(request.user, Person):
            get_object_or_404(ChatPerson, chat=chat_id, person=request.user)
        else:
            chat_id = request.user.id
        messages = Message.objects.filter(chat=chat_id)
        messages_data = reversed(list(MessageSerializer(messages, many=True).data))
        return Response(messages_data, status=status.HTTP_200_OK)

    def post(self, request, chat_id):
        # Get Sender and Chat
        user = None
        if isinstance(request.user, Person):
            user = request.user
            get_object_or_404(ChatPerson, chat=chat_id, person=user)
        chat = get_object_or_404(Chat, project=request.auth.pk, id=chat_id)

        # Filter for no attachments or text
        if len(request.FILES.getlist('attachments')) == 0 and request.data.get('text', None) is None:
            return Response({'message': 'bad data'}, status=status.HTTP_400_BAD_REQUEST)

        # Save new Message
        serializer = MessageSerializer(data=request.data)
        if serializer.is_valid():
            message = serializer.save(chat=chat, sender=user)

            # Attach files objects
            if request.FILES.get('attachments', None) is not None:
                for attachment in request.FILES.getlist('attachments'):
                    Attachment.objects.create(chat=chat, message=message, file=attachment)

            # OR Attach files URLs
            if len(request.data.get('attachment_urls', [])) > 0:
                for url in request.data['attachment_urls']:
                    try:
                        file, _ = urlretrieve(url)
                        file_name = os.path.basename(urlparse(url).path)
                        attachment = Attachment.objects.create(chat=chat, message=message)
                        attachment.file.save(file_name, File(open(file, 'rb')))
                        urlcleanup()
                    except HTTPError as e:
                        pass
                    except ValueError as e:
                        pass

            # Update chats for people
            chat_people = ChatPerson.objects.filter(chat=chat)
            for chat_person in chat_people:
                chat_person.last_read = message if chat_person.person == user else chat_person.last_read
                chat_person.chat_updated = message.created
                chat_person.save()

            people = [chat_person.person for chat_person in chat_people]
            people_ids = [person.id for person in people]
            chat_serializer = ChatSerializer(chat, many=False)

            # Publish new data (Socket + Hooks + Emails)
            chat_publisher.publish_chat_data('edit_chat', chat_serializer.data, people_ids=people_ids)
            chat_publisher.publish_message_data('new_message', chat, serializer.data, people_ids=people_ids)
            emailer = Emailer()
            emailer.email_chat_members(project=request.auth, message=message, people=people)

            # Tracking
            mix_panel.track(str(request.auth.owner), 'new message')

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LatestMessages(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication, ChatAccessKeyAuthentication,)

    def get(self, request, chat_id, count):
        if isinstance(request.user, Person):
            get_object_or_404(ChatPerson, chat=chat_id, person=request.user)
        else:
            chat_id = request.user.id
        messages = Message.objects.filter(chat=chat_id)[:int(count)]
        messages_data = reversed(list(MessageSerializer(messages, many=True).data))
        return Response(messages_data, status=status.HTTP_200_OK)
    # TODO: You can make another PUT request where you get messages LT the last PK


class MessageDetails(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication, ChatAccessKeyAuthentication,)

    def get(self, request, chat_id, message_id):
        if isinstance(request.user, Chat):
            message = get_object_or_404(Message, chat=request.user, id=message_id)
        else:
            get_object_or_404(ChatPerson, chat=chat_id, person=request.user)
            chat = get_object_or_404(Chat, project=request.auth.pk, id=chat_id)
            message = get_object_or_404(Message, chat=chat, id=message_id)
        serializer = MessageSerializer(message, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, chat_id, message_id):
        chat = get_object_or_404(Chat, project=request.auth.pk, id=chat_id)
        if isinstance(request.user, Chat):
            message = get_object_or_404(Message, chat=request.user, id=message_id)
        else:
            get_object_or_404(ChatPerson, chat=chat_id, person=request.user)
            message = get_object_or_404(Message, chat=chat, id=message_id, sender=request.user)

        serializer = MessageSerializer(message, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            mix_panel.track(str(request.user), 'edit message')
            chat_publisher.publish_message_data('edit_message', chat, serializer.data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, chat_id, message_id):
        chat = get_object_or_404(Chat, project=request.auth.pk, id=chat_id)
        if isinstance(request.user, Chat):
            message = get_object_or_404(Message, chat=chat, id=message_id, sender=None)
        else:
            message = get_object_or_404(Message, chat=chat, id=message_id, sender=request.user)

        message_json = MessageSerializer(message, many=False).data
        mix_panel.track(str(request.user), 'delete message')
        chat_publisher.publish_message_data('delete_message', chat, message_json)
        message.delete()  # Delete after publish!
        return Response(message_json, status=status.HTTP_200_OK)
