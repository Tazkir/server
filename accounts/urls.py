from django.conf.urls import url
from . import views

app_name = 'accounts'

urlpatterns = [
    url(r'^$', views.Accounts.as_view()),
    url(r'^me/$', views.MyDetails.as_view()),
    url(r'^login/$', views.CustomObtainAuthToken.as_view()),
    url(r'^(?P<reset_uuid>^([A-Fa-f0-9]{8})(-[A-Fa-f0-9]{4}){3}-[A-Fa-f0-9]{12})/$', views.ResetAccount.as_view()),
    url(r'^demos/$', views.Demos.as_view()),
]
