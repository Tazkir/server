from django.conf.urls import url
from . import views

app_name = 'feedback'

urlpatterns = [
    url(r'^$', views.FeedbackList.as_view()),
]
