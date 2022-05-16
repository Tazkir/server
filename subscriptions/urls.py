from django.conf.urls import url
from . import views

app_name = 'subscriptions'

urlpatterns = [
    url(r'^(?P<project_id>[\w\-]+)/$', views.CreateSubscription.as_view()),
]
