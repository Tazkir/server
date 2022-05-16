import json
import uuid
import autobahn

from channels.consumer import AsyncConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from django.http import Http404
from django.shortcuts import get_object_or_404

from chats.models import Chat


def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


def is_valid_int(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


def is_valid_str(val):
    try:
        str(val)
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


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        data = query_string_parse(self.scope['query_string'])
        project_id = data.get('projectID', False)
        access_key = data.get('accessKey', False)
        chat_id = data.get('chatID', False)
        chat = None

        if is_valid_uuid(project_id) and is_valid_int(chat_id) and is_valid_str(access_key):
            try:
                chat = await self.get_chat_or_404(project_id, chat_id, access_key)
                await self.channel_layer.group_add(
                    "chat_"+str(chat.id),
                    self.channel_name
                )

            except Http404 as error:
                print('Connect exception: {}'.format(str(error)))

        await self.accept()

        if chat is None:
            await self.send(text_data=json.dumps({"action": "login_error"}))

    async def receive(self, text_data=None, bytes_data=None):
        if '"ping"' in text_data:
            await self.send(text_data=json.dumps({"action": "pong"}))

    async def disconnect(self, code):
        data = query_string_parse(self.scope['query_string'])
        project_id = data.get('projectID', False)
        access_key = data.get('accessKey', False)
        chat_id = data.get('chatID', False)
        chat = await self.get_chat_or_404(project_id, chat_id, access_key)
        await self.channel_layer.group_discard("chat_"+str(chat.id), self.channel_name)

        # await self.close()
        return await super().disconnect(code)

    async def dispatch_data(self, event):
        await self.send(text_data=json.dumps({
            "action": event["action"],
            "data": event["data"]
        }))

    @database_sync_to_async
    def get_chat_or_404(self, project_id, chat_id, access_key):
        # TODO: Add type checks
        return get_object_or_404(Chat, project=project_id, id=chat_id, access_key=access_key)

    async def send(self, *args, **kwargs):
        try:
            await super().send(*args, **kwargs)
        except autobahn.exception.Disconnected:
            await self.close()


class ChatConsumer2(AsyncConsumer):
    def get_connection_id(self, key_values):
        key_values = key_values.decode("utf-8").split('&')
        key_values = dict(key_value.split('=') for key_value in key_values)
        return key_values['connection_id']

    async def websocket_connect(self, event):
        connection_id = self.get_connection_id(self.scope['query_string'])
        if connection_id is not None:
            await self.channel_layer.group_add("connection_"+str(connection_id), self.channel_name)
            await self.send({"type": "websocket.accept"})

    async def websocket_receive(self, event):
        try:
            auth = json.loads(event['text'])
            project_id = auth['project-id']
            chat_id = auth['chat-id']
            access_key = auth['access-key']

            if is_valid_uuid(project_id) and is_valid_int(chat_id) and is_valid_str(access_key):
                chat = await self.get_chat_or_404(project_id, chat_id, access_key)
                await self.channel_layer.group_add("chat_"+str(chat.id), self.channel_name)
                if chat is None:
                    await self.send({
                        "type": "websocket.send",
                        "text": json.dumps({"action": "login_error"})
                    })
                else:
                    await self.send({
                        "type": "websocket.send",
                        "text": json.dumps({"action": 'login_success'})
                    })

        except KeyError:
            pass

        except Http404:
            pass

    async def dispatch_data(self, event):
        await self.send({
            "type": "websocket.send",
            "text": json.dumps({"action": event["action"], "data": event["data"]})
        })

    async def websocket_disconnect(self, event):
        data = query_string_parse(self.scope['query_string'])
        project_id = data.get('projectID', False)
        access_key = data.get('accessKey', False)
        chat_id = data.get('chatID', False)
        chat = await self.get_chat_or_404(project_id, chat_id, access_key)
        await self.channel_layer.group_discard("chat_"+str(chat.id), self.channel_name)

    @database_sync_to_async
    def get_chat_or_404(self, project_id, chat_id, access_key):
        # TODO: Add type checks
        return get_object_or_404(Chat, project=project_id, id=chat_id, access_key=access_key)
