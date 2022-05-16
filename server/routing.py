"""
This file is for configuring channels as an ASGI application
"""
from users.consumers import PersonConsumer, PersonConsumer2, PersonConsumer4
from chats.consumers import ChatConsumer
from django.urls import re_path
from channels.security.websocket import AllowedHostsOriginValidator
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter


application = ProtocolTypeRouter({
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                re_path(r"^chat/$", ChatConsumer.as_asgi()),
                re_path(r"^person/$", PersonConsumer.as_asgi()),
                re_path(r"^person_v2/$", PersonConsumer2.as_asgi()),
                re_path(r"^person_v3/$", PersonConsumer4.as_asgi()),
                re_path(r"^person_v4/$", PersonConsumer4.as_asgi()),
            ])
        )
    )
})
