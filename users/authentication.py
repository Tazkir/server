
from rest_framework import authentication

from django.contrib.auth.hashers import check_password

from projects.models import Project, Person
from chats.models import Chat


def get_chat_id(request):
    try:
        routes = request.path.split('/')
        if routes[1] == 'chats' and routes[2] != '':
            return int(routes[2])
        return None

    except ValueError:
        return None


class UserSecretAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        public_key = request.headers.get('public-key', None)
        public_key = public_key if public_key else request.headers.get('project-id', None)
        private_key = request.headers.get('private-key', None)
        username = request.headers.get('user-name', None)
        secret = request.headers.get('user-secret', None)

        try:
            if public_key is not None:
                project = Project.objects.get(public_key=public_key)

                if not project.is_active:
                    raise Exception

                user = Person.objects.get(project=project, username=username)
                if not check_password(secret, user.secret):
                    raise Exception(Person.DoesNotExist, '')
                return user, project

            if private_key is not None:
                project = Project.objects.get(private_key=private_key)

                if not project.is_active:
                    raise Exception

                chat_id = get_chat_id(request=request)

                if username is not None:
                    user = Person.objects.get(project=project, username=username)
                    return user, project
                elif chat_id is not None:
                    chat = Chat.objects.get(id=chat_id)
                    return chat.admin, project
                else:
                    try:
                        user = Person.objects.filter(project=project)[:1][0]
                        return user, project
                    except IndexError:
                        return None, project

            return None

        except:
            return None
