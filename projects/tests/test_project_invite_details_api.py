from rest_framework.utils import json
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from projects.models import User, Project, Collaborator, Invite
from projects.views import InviteDetailsWeb

USER_EMAIL = 'adam@gmail.com'
USER_PASSWORD = 'potato_123'

PROJECT_1 = "Chat Engine 1"

USER_EMAIL_2 = 'adam2@gmail.com'
USER_PASS_2 = 'potato_1234'


class GetProjectInviteTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.new_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.collaborator = Collaborator.objects.get(user=self.user, project=self.project)
        self.invite = Invite.objects.create(to_email=self.new_user.email, project=self.project, role='admin')

    def test_get_project_invite(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.get('/projects/{}/invites/'.format(self.invite.pk))
        force_authenticate(request, user=self.user)
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['to_email'], USER_EMAIL_2)
        self.assertEqual(response.data['role'], 'admin')

    def test_get_project_invite_needs_no_auth(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.get('/projects/{}/invites/'.format(self.invite.pk))
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)

    def test_get_project_invite_must_collaborator_not_needed(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.get('/projects/{}/invites/'.format(self.invite.pk))
        force_authenticate(request, user=self.new_user)
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)


class PatchProjectInviteTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.new_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.collaborator = Collaborator.objects.get(user=self.user, project=self.project)
        self.invite = Invite.objects.create(to_email=self.new_user.email, project=self.project, role='admin')

    def test_patch_project_invite(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.patch(
            '/projects/invites/{}/'.format(self.invite.access_key),
            json.dumps({"role": 'member'}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['to_email'], USER_EMAIL_2)
        self.assertEqual(response.data['role'], 'member')

    def test_patch_project_invite_needs_no_auth(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.patch(
            '/projects/invites/{}/'.format(self.invite.access_key),
            json.dumps({"role": 'member'}),
            content_type='application/json'
        )
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)

    def test_patch_project_invite_admin_not_needed(self):
        self.collaborator.role = 'not admin'
        self.collaborator.save()

        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.patch(
            '/projects/invites/{}/'.format(self.invite.access_key),
            json.dumps({"role": 'member'}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)


class PutProjectInviteTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.new_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.collaborator = Collaborator.objects.get(user=self.user, project=self.project)
        self.invite = Invite.objects.create(to_email=self.new_user.email, project=self.project, role='admin')

    def test_apply_project_invite(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.put('/projects/invites/{}/'.format(self.invite.access_key))
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['title'], PROJECT_1)
        self.assertEqual(len(Invite.objects.all()), 0)
        self.assertEqual(len(Collaborator.objects.all()), 2)

    def test_apply_project_invalid_invite(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.put('/projects/invites/{}/'.format('...'))
        response = view(request, invite_key='...')

        self.assertEqual(response.status_code, 404)
        self.assertEqual(len(Invite.objects.all()), 1)
        self.assertEqual(len(Collaborator.objects.all()), 1)


class DeleteProjectInviteTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER_EMAIL, password=USER_PASSWORD)
        self.new_user = User.objects.create_user(email=USER_EMAIL_2, password=USER_PASS_2)
        self.project = Project.objects.create(owner=self.user, title=PROJECT_1)
        self.collaborator = Collaborator.objects.get(user=self.user, project=self.project)
        self.invite = Invite.objects.create(to_email=self.new_user.email, project=self.project, role='admin')

    def test_delete_project_invite(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.delete('/projects/invites/{}/'.format(self.invite.access_key))
        force_authenticate(request, user=self.user)
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(len(Invite.objects.all()), 0)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['to_email'], USER_EMAIL_2)
        self.assertEqual(response.data['role'], 'admin')

    def test_delete_project_invite_needs_no_auth(self):
        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.delete('/projects/invites/{}/'.format(self.invite.access_key))
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)

    def test_delete_project_invite_admin_not_needed(self):
        self.collaborator.role = 'not admin'
        self.collaborator.save()

        factory = APIRequestFactory()
        view = InviteDetailsWeb.as_view()
        request = factory.delete('/projects/invites/{}/'.format(self.invite.access_key))
        force_authenticate(request, user=self.user)
        response = view(request, invite_key=self.invite.access_key)

        self.assertEqual(response.status_code, 200)
