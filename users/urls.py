from django.conf.urls import url
from . import views

app_name = 'users'

urlpatterns = [
    url(r'^me/$', views.MyDetails.as_view()),
    url(r'^me/session/$', views.MySession.as_view()),
    url(r'^$', views.PeoplePrivateApi.as_view()),
    url(r'^(?P<person_id>[0-9]+)/$', views.PersonPrivateApi.as_view()),
]
