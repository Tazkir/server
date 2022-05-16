import json

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate

from projects.models import User

from feedback.views import FeedbackList, Feedback

USER = 'adam@gmail.com'
PASSWORD = 'potato_123'
FEEDBACK = "Boo you SUCK"


class GetFeedbackTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)

    def test_get_feedback(self):
        factory = APIRequestFactory()
        view = FeedbackList.as_view()
        request = factory.get('/feedback/')
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        Feedback.objects.create(user=self.user, text=FEEDBACK)

        response = view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['text'], FEEDBACK)

    def test_get_feedback_needs_auth(self):
        factory = APIRequestFactory()
        view = FeedbackList.as_view()
        request = factory.get('/feedback/')
        response = view(request)

        self.assertEqual(response.status_code, 401)


class PostFeedbackTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=USER, password=PASSWORD)

    def test_post_feedback(self):
        self.assertEqual(len(Feedback.objects.all()), 0)

        factory = APIRequestFactory()
        view = FeedbackList.as_view()
        request = factory.post(
            '/feedback/',
            json.dumps({"text": FEEDBACK}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(Feedback.objects.all()), 1)
        self.assertEqual(response.data['text'], FEEDBACK)

    def test_get_feedback_needs_text(self):
        self.assertEqual(len(Feedback.objects.all()), 0)

        factory = APIRequestFactory()
        view = FeedbackList.as_view()
        request = factory.post(
            '/feedback/',
            json.dumps({}),
            content_type='application/json'
        )
        force_authenticate(request, user=self.user)
        response = view(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(len(Feedback.objects.all()), 0)

    def test_get_feedback_needs_auth(self):
        self.assertEqual(len(Feedback.objects.all()), 0)

        factory = APIRequestFactory()
        view = FeedbackList.as_view()
        request = factory.post(
            '/feedback/',
            json.dumps({"text": FEEDBACK}),
            content_type='application/json'
        )
        response = view(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(len(Feedback.objects.all()), 0)
