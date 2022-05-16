from django.conf.urls import url

from . import views

app_name = 'webhooks'

urlpatterns = [
    url(r'^$', views.Webhooks.as_view()),
    url(r'^test/$', views.WebhookTest.as_view()),

    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/$', views.WebhooksWeb.as_view()),
    url(r'^(?P<project_id>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/(?P<event_trigger>((?:[A-Za-z_ -]|%20)+))/$', views.WebhookDetailsWeb.as_view()),
]
