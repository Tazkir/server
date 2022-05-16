from projects.models import Project

from rest_framework import exceptions, authentication
from rest_framework.authtoken.models import Token


class PrivateKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        private_key = request.headers.get('private-key', None)

        if private_key is not None:
            try:
                project = Project.objects.get(private_key=private_key)

                if not project.is_active:
                    raise Exception

                return project.owner, project

            except Project.DoesNotExist:
                raise exceptions.AuthenticationFailed(detail='No such user')

            except Exception as ex:
                raise exceptions.AuthenticationFailed(detail=ex)

        return None


class TokenProjectAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        token = request.headers.get('authorization', '').lower().replace("token ", "")

        project = None
        try:
            project_id = request.get_full_path().split('/projects/')[1].split('/')[0]
            project = Project.objects.get(pk=project_id)
        except:
            pass

        # TODO: Get or 404 collaborator here no?

        if token is not None:
            try:
                token = Token.objects.get(key=token)
                return token.user, project

            except Token.DoesNotExist:
                raise exceptions.AuthenticationFailed(detail='No such token')

            except Exception as ex:
                raise exceptions.AuthenticationFailed(detail=ex)

        return None
