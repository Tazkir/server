from users.serializers import SessionSerializer
from rest_framework.throttling import UserRateThrottle
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from django.db import IntegrityError
from django.shortcuts import get_object_or_404

from projects.models import Person
from projects.serializers import PersonSerializer
from projects.authentication import PrivateKeyAuthentication

from chats.models import ChatPerson
from chats.serializers import ChatSerializer

from users.models import Session
from users.serializers import SessionSerializer

from tracking.mixpanel import mix_panel

from .authentication import UserSecretAuthentication
from .publishers import chat_publisher


class MyDetails(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication,)

    def get(self, request):
        serializer = PersonSerializer(request.user, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = PersonSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            for chat_person in ChatPerson.objects.filter(person=request.user):
                chat_data = ChatSerializer(chat_person.chat, many=False).data
                mix_panel.track(str(request.user), 'edit person')
                chat_publisher.publish_chat_data('edit_chat', chat_data)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        person = request.user
        person_json = PersonSerializer(person, many=False).data
        person.delete()
        mix_panel.track(str(request.user), 'delete person api')
        return Response(person_json, status=status.HTTP_200_OK)


class MySession(APIView):
    throttle_scope = 'burst'
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (UserSecretAuthentication,)

    def get(self, request):
        session = Session.objects.get_or_create(person=request.user)[0]
        session.save()
        serializer = SessionSerializer(session, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PeoplePrivateApi(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (PrivateKeyAuthentication,)

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
        people = Person.objects.filter(project=request.auth.pk)[start:end]
        serializer = PersonSerializer(people, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            match = Person.objects.filter(project=request.auth, username=request.data.get('username', None))
            if match.exists():
                return Response({'message': "This username is taken."}, status=status.HTTP_400_BAD_REQUEST)
            try:
                serializer.save(project=request.auth)
                mix_panel.track(str(request.user), 'new person api')
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({'message': 'This user exists'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = PersonSerializer(data=request.data)

        match = Person.objects.filter(project=request.auth, username=request.data.get('username', None))
        if match.exists():
            serializer = PersonSerializer(match[0], many=False)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if serializer.is_valid():
            serializer.save(project=request.auth)
            mix_panel.track(str(request.user), 'new person api')
            return Response(serializer.data, status=status.HTTP_201_CREATED)


class PersonPrivateApi(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (PrivateKeyAuthentication,)

    def get(self, request, person_id):
        person = get_object_or_404(Person, project=request.auth, pk=person_id)
        serializer = PersonSerializer(person, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, person_id):
        person = get_object_or_404(Person, project=request.auth, pk=person_id)

        match = Person.objects.filter(project=request.auth, username=request.data.get('username', None))
        if match.exists() and match[0].pk != person.pk:
            return Response({'message': "This username is taken."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PersonSerializer(person, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            mix_panel.track(str(request.user), 'edit person api')
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, person_id):
        person = get_object_or_404(Person, project=request.auth, pk=person_id)
        person_json = PersonSerializer(person, many=False).data
        person.delete()
        mix_panel.track(str(request.user), 'delete person api')
        return Response(person_json, status=status.HTTP_200_OK)
