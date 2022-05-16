from rest_framework import exceptions, authentication

from projects.models import Project
from chats.models import Chat


def get_chat_id(request):
    try:
        routes = request.path.split('/')
        if routes[1] == 'chats' and routes[2] != '':
            return int(routes[2])
        return None

    except ValueError:
        return None


class ChatAccessKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        public_key = request.headers.get('public-key', None)
        public_key = public_key if public_key else request.headers.get('project-id', None)
        private_key = request.headers.get('private-key', None)
        chat_id = get_chat_id(request)
        access_key = request.headers.get('access-key', None)

        try:
            if public_key is not None:
                project = Project.objects.get(public_key=public_key)
                chat = Chat.objects.get(project=project, id=chat_id, access_key=access_key)

                if not project.is_active:
                    raise Exception

                return chat, project

            if private_key is not None:
                project = Project.objects.get(private_key=private_key)
                chat = Chat.objects.get(project=project, id=chat_id)

                if not project.is_active:
                    raise Exception

                return chat, project

            return None

        except Project.DoesNotExist:
            return None

        except Chat.DoesNotExist:
            return None

        except Exception as ex:
            raise exceptions.AuthenticationFailed(detail=ex)
