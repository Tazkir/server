from datetime import datetime, timedelta
import uuid
import pytz
import json

from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist

from tracking.mixpanel import mix_panel

from .models import User, Reset
from .notifiers import Emailer
from .serializers import UserSerializer, UserPublicSerializer
from accounts import notifiers

emailer = Emailer()


def health_check(request):
    return HttpResponse(f"<h1>Welcome!</h1>")


class CustomObtainAuthToken(ObtainAuthToken, APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        request.data['username'] = request.data.pop('email').lower()
        response = super(CustomObtainAuthToken, self).post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        user = User.objects.get(email=request.data['username'])
        serializer = UserSerializer(user)
        return Response({'token': token.key, 'user': serializer.data}, status=status.HTTP_200_OK)


class Accounts(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        email = request.data['email'].lower() if request.data['email'] else None
        if User.objects.filter(email=email):
            return Response({'message': 'That email is already used'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            user = User.objects.get(email=email)
            token = Token.objects.create(user=user)
            mix_panel.track(str(user), 'sign up')
            return Response({"user": serializer.data, "token": token.key}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        email = request.data['email'].lower() if request.data['email'] else None
        try:
            user = User.objects.get(email=email)
            query = Reset.objects.get_or_create(user=user)
            now = datetime.now().replace(tzinfo=pytz.UTC)
            query[0].uuid = uuid.uuid4()
            query[0].expiry = now + timedelta(hours=1)
            query[0].save()
            emailer.email_reset_link(user, query[0])
        except ObjectDoesNotExist:
            pass
        return Response({"message": "Reset link was sent if the user exists."}, status=status.HTTP_200_OK)


class MyDetails(APIView):
    throttle_classes = [UserRateThrottle]
    permission_classes = (permissions.IsAuthenticated,)
    authentication_classes = (TokenAuthentication, SessionAuthentication)

    def get(self, request):
        serializer = UserPublicSerializer(request.user, many=False)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            mix_panel.track(str(request.user), 'edit account')
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user_json = UserSerializer(request.user, many=False).data
        mix_panel.track(str(request.user), 'delete account')
        request.user.delete()
        return Response(user_json, status=status.HTTP_200_OK)


class ResetAccount(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.AllowAny,)

    def get(self, request, reset_uuid):
        now = datetime.now().replace(tzinfo=pytz.UTC)
        reset = get_object_or_404(Reset, uuid=reset_uuid, expiry__gt=now)
        serializer_data = UserSerializer(reset.user, many=False).data
        token = Token.objects.get(user=reset.user)
        mix_panel.track(str(reset.user), 'reset password')
        reset.delete()
        return Response({"user": serializer_data, "token": token.key}, status=status.HTTP_200_OK)


class Demos(APIView):
    throttle_classes = [AnonRateThrottle]
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        data = json.loads(request.body)
        emailer.email_demo_requested(
            email=data.get('email', ''),
            company=data.get('company', ''),
            userbase=data.get('userbase', ''),
            goals=data.get('goals', '')
        )
        return Response({"message": "request sent"}, status=status.HTTP_200_OK)
