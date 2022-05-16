
from django.contrib import admin
from .models import Chat, ChatPerson, Person, Message, Attachment

admin.site.register(Chat)
admin.site.register(ChatPerson)
admin.site.register(Person)

admin.site.register(Message)
admin.site.register(Attachment)
