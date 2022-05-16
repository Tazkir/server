from django.conf.urls import url

from users.views import PeoplePrivateApi, PersonPrivateApi

from . import views

app_name = 'projects'

urlpatterns = [
    url(r'^$', views.Projects.as_view()),

    url(r'^people/$', PeoplePrivateApi.as_view()),
    url(r'^people/(?P<person_id>[0-9]+)/$', PersonPrivateApi.as_view()),

    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/$', views.ProjectDetails.as_view()),

    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/collaborators/$', views.ProjectCollaboratorsWeb.as_view()),
    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/collaborators/(?P<collaborator_id>[0-9]+)/$', views.CollaboratorsDetailsWeb.as_view()),

    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/invites/$', views.ProjectInvitesWeb.as_view()),
    url(r'^invites/(?P<invite_key>.+)/$', views.InviteDetailsWeb.as_view()),

    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/people/$', views.ProjectPeopleWeb.as_view()),
    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/people/(?P<person_id>[0-9]+)/$', views.PersonDetailsWeb.as_view()),

    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/chats/$', views.ChatsWeb.as_view()),
    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/chats/(?P<chat_id>[0-9]+)/$', views.ChatDetailsWeb.as_view()),

    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/message_count/$', views.MessageCount.as_view()),
    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/private_key/$', views.PrivateKeyDetails.as_view()),
]
