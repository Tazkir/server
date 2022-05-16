"""server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path

from accounts.views import health_check


urlpatterns = [
    path('admin/', admin.site.urls),
    # Added routes
    url(r'^accounts/', include('accounts.urls', namespace='accounts')),
    url(r'^chats/', include('chats.urls', namespace='chats')),
    url(r'^crons/', include('crons.urls', namespace='crons')),
    url(r'^feedback/', include('feedback.urls', namespace='feedback')),
    url(r'^projects/', include('projects.urls', namespace='projects')),
    url(r'^users/?', include('users.urls', namespace='users')),  # Add ? for YouTube tutorial fuckup https://www.youtube.com/watch?v=Bv9Js3QLOLY&t=383s
    url(r'^subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    url(r'^webhooks/', include('webhooks.urls', namespace='webhooks')),
    # Home View
    path('', health_check),
]
