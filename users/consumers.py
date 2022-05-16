import json
import uuid
import autobahn

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.hashers import check_password

from users.models import Session
from projects.models import Person, Connection


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def query_string_parse(key_values):
    try:
        results = {}
        key_values = key_values.decode("utf-8")

        for query in key_values.split('&'):
            key_val = query.split('=')
            results[key_val[0]] = key_val[1]

        return results

    except Exception as e:
        print(f'Error: {e}')
        return None


class PersonConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        data = query_string_parse(self.scope['query_string'])
        project_id = data.get('publicKey', False)
        username = data.get('username', False)
        secret = data.get('secret', False)
        person = None

        if project_id and username and secret and is_valid_uuid(project_id):
            try:
                person = await self.get_person_or_404(project_id, username, secret)
                await self.update_online_status(person, True)
                await self.channel_layer.group_add(
                    "user_"+str(person.id),
                    self.channel_name
                )

            except Http404 as error:
                print('Connect exception: {}'.format(str(error)))

        await self.accept()

        if person is None:
            await self.send(text_data=json.dumps({"action": "login_error"}))

    async def receive(self):
        pass

    async def disconnect(self, code):
        data = query_string_parse(self.scope['query_string'])
        project_id = data['publicKey']
        username = data['username']
        secret = data['secret']

        try:
            person = await self.get_person_or_404(project_id, username, secret)
            await self.update_online_status(person, False)
            await self.channel_layer.group_discard("user_"+str(person.id), self.channel_name)

        except Exception:
            return
        
        return await super().disconnect(code)

    @database_sync_to_async
    def update_online_status(self, person, status):
        person.is_online = status
        person.save()

    @database_sync_to_async
    def get_person_or_404(self, project_id, username, secret):
        # TODO: Add type checks
        person = get_object_or_404(Person, project=project_id, username=username)
        if check_password(secret, person.secret):
            return person
        else:
            raise Http404
    
    async def dispatch_data(self, event):
       await self.send(text_data=json.dumps({
            "action": event["action"],
            "data": event["data"]
        }))

    async def send(self, *args, **kwargs):
        try:
            await super().send(*args, **kwargs)
        except autobahn.exception.Disconnected:
            await self.close()


class PersonConsumer2(AsyncWebsocketConsumer):
    def get_connection_id(self, key_values):
        key_values = key_values.decode("utf-8").split('&')
        key_values = dict(key_value.split('=') for key_value in key_values)
        return key_values['connection_id']

    async def connect(self):
        connection_id = self.get_connection_id(self.scope['query_string'])
        if connection_id is not None:
            await self.get_or_create_connection(connection_id)
            await self.channel_layer.group_add("connection_"+str(connection_id), self.channel_name)
            await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            connection_id = self.get_connection_id(self.scope['query_string'])
            auth = json.loads(text_data)
            project_id = auth['project-id']
            username = auth['user-name']
            secret = auth['user-secret']
        except KeyError:
            return await self.login_fail()

        if project_id and username and secret and is_valid_uuid(project_id):
            try:
                person = await self.get_person_or_404(project_id, username, secret)
            except Http404:
                return await self.login_fail()

            connection = await self.get_or_create_connection(connection_id)
            await self.set_connection(connection, person)
            await self.update_online_status(person, True)
            await self.channel_layer.group_add("user_"+str(person.id), self.channel_name)
            self.send(text_data=json.dumps({"action": "login_success"}))
        else:
            return await self.login_fail()

    async def dispatch_data(self, event):
        await self.send(text_data=json.dumps({
            "action": event["action"],
            "data": event["data"]
        }))

    async def login_fail(self):
        self.send(text_data=json.dumps({"action": "login_error"}))
        return None
    
    async def send(self, *args, **kwargs):
        try:
            await super().send(*args, **kwargs)
        except autobahn.exception.Disconnected:
            await self.close()

    async def disconnect(self, code):
        connection_id = self.get_connection_id(self.scope['query_string'])

        if connection_id is not None:
            connection = await self.get_or_create_connection(connection_id)
            person = await self.get_connection_person(connection)

            await self.update_online_status(person, False)
            await self.delete_connection(connection)
            await self.channel_layer.group_discard("user_"+str(person.id), self.channel_name)

        return await super().disconnect(code)

    @database_sync_to_async
    def get_or_create_connection(self, connection_id):
        connection_created = Connection.objects.get_or_create(id=connection_id)
        return connection_created[0]

    @database_sync_to_async
    def get_connection_person(self, connection):
        return connection.person

    @database_sync_to_async
    def set_connection(self, connection, person):
        connection.person = person
        connection.save()

    @database_sync_to_async
    def delete_connection(self, connection):
        connection.delete()

    @database_sync_to_async
    def update_online_status(self, person, status):
        if person is not None:
            person.is_online = status
            person.save()

    @database_sync_to_async
    def get_person_or_404(self, project_id, username, secret):
        # TODO: Add type checks
        person = get_object_or_404(Person, project=project_id, username=username)
        if check_password(secret, person.secret):
            return person
        else:
            raise Http404


# class PersonConsumer3(AsyncConsumer):
#     def get_session_token(self, key_values):
#         key_values = key_values.decode("utf-8").split('&')
#         key_values = dict(key_value.split('=') for key_value in key_values)
#         return key_values.get('session_token', '')

#     async def websocket_connect(self, event):
#         session_token = self.get_session_token(self.scope['query_string'])
#         session = await self.get_session(session_token)

#         if session is not None:
#             person = await self.get_session_person(session)
#             await self.channel_layer.group_add("user_"+str(person.id), self.channel_name)
#             await self.update_online_status(person, True)
#             await self.send({"type": "websocket.accept"})

#         else:
#             await self.send({"type": "websocket.accept"})
#             await self.send({
#                 "type": "websocket.send",
#                 "text": json.dumps({"action": "login_error"})
#             })

#     async def websocket_receive(self, event):
#         if str(event['text']) == '"ping"':
#             await self.send({
#                 "type": "websocket.send",
#                 "text": json.dumps({"action": "pong"})
#             })

#     async def websocket_disconnect(self, event):
#         session_token = self.get_session_token(self.scope['query_string'])
#         session = await self.get_session(session_token)

#         if session is not None:
#             person = await self.get_session_person(session)

#             await self.update_online_status(person, False)
#             await self.channel_layer.group_discard("user_"+str(person.id), self.channel_name)

#     async def dispatch_data(self, event):
#         await self.send({
#             "type": "websocket.send",
#             "text": json.dumps({"action": event["action"], "data": event["data"]})
#         })

#     @database_sync_to_async
#     def get_session(self, session_token):
#         try:
#             return Session.objects.get(token=session_token)
#         except:
#             return None

#     @database_sync_to_async
#     def get_session_person(self, session):
#         return session.person

#     @database_sync_to_async
#     def update_online_status(self, person, status):
#         if person is not None:
#             person.is_online = status
#             person.save()


class PersonConsumer4(AsyncWebsocketConsumer):
    def get_session_token(self, key_values):
        key_values = key_values.decode("utf-8").split('&')
        key_values = dict(key_value.split('=') for key_value in key_values)
        return key_values.get('session_token', '')

    async def connect(self):
        session_token = self.get_session_token(self.scope['query_string'])
        session = await self.get_session(session_token)

        if session is not None:
            person = await self.get_session_person(session)
            await self.channel_layer.group_add("user_"+str(person.id), self.channel_name)
            await self.update_online_status(person, True)
            await self.accept()

        else:
            await self.accept()
            await self.send(text_data=json.dumps({"action": "login_error"}))

    async def receive(self, text_data=None, bytes_data=None):
        if '"ping"' in text_data:
            await self.send(text_data=json.dumps({"action": "pong"}))

        return super().receive(text_data=text_data, bytes_data=bytes_data)

    async def disconnect(self, code):
        session_token = self.get_session_token(self.scope['query_string'])
        session = await self.get_session(session_token)

        if session is not None:
            person = await self.get_session_person(session)

            await self.update_online_status(person, False)
            await self.channel_layer.group_discard("user_"+str(person.id), self.channel_name)

        # await self.close()
        return super().disconnect(code)

    async def dispatch_data(self, event):
        await self.send(text_data=json.dumps({
            "action": event["action"],
            "data": event["data"]
        }))

    @ database_sync_to_async
    def get_session(self, session_token):
        try:
            return Session.objects.get(token=session_token)
        except:
            return None

    @ database_sync_to_async
    def get_session_person(self, session):
        return session.person

    @ database_sync_to_async
    def update_online_status(self, person, status):
        if person is not None:
            person.is_online = status
            person.save()

    async def send(self, *args, **kwargs):
        try:
            await super().send(*args, **kwargs)
        except autobahn.exception.Disconnected:
            await self.close()
