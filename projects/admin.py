
from django.contrib import admin
from .models import Project, Collaborator, Invite

admin.site.register(Project)
admin.site.register(Collaborator)
admin.site.register(Invite)
