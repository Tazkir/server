from django.conf.urls import url
from . import views

app_name = 'chats'

urlpatterns = [
    url(r'^$', views.Chats.as_view()),
    url(r'^latest/(?P<count>[0-9]+)/$', views.LatestChats.as_view()),
    url(r'^(?P<chat_id>[0-9]+)/$', views.ChatDetails.as_view()),
    url(r'^(?P<chat_id>[0-9]+)/typing/$', views.ChatTyping.as_view()),
    url(r'^(?P<chat_id>[0-9]+)/people/$', views.ChatPersonList.as_view()),
    url(r'^(?P<chat_id>[0-9]+)/others/$', views.OtherChatPersonList.as_view()),
    url(r'^(?P<chat_id>[0-9]+)/messages/$', views.Messages.as_view()),
    url(r'^(?P<chat_id>[0-9]+)/messages/(?P<message_id>[0-9]+)/$', views.MessageDetails.as_view()),
    url(r'^(?P<chat_id>[0-9]+)/messages/latest/(?P<count>[0-9]+)/$', views.LatestMessages.as_view()),
]
