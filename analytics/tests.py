from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Question


class QuestionReportViewSetTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='reporter',
            email='reporter@example.com',
            password='test-password',
        )
        self.question = Question.objects.create(
            serial_number='Q-REPORT-1',
            content='What is 2 + 2?',
        )
        self.base_url = f'/api/questions/{self.question.public_id}/reports/'

    def test_create_report_sets_request_user_when_consent_true(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'report_reasons': ['Formatting of text'],
            'additional_details': 'Some symbols are unreadable.',
        }

        response = self.client.post(self.base_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['username'], self.user.username)
        self.assertEqual(
            response.data['report_reasons'],
            ['Formatting of text'],
        )
        self.assertEqual(str(response.data['question']), str(self.question.public_id))

    def test_create_report_does_not_set_user_when_contact_consent_false(self):
        self.client.force_authenticate(user=self.user)
        payload = {
            'report_reasons': ['Question incorrect or confusing'],
            'contact_consent': False,
        }

        response = self.client.post(self.base_url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data['user'])

    def test_partial_update_replaces_report_reasons(self):
        self.client.force_authenticate(user=self.user)
        create_payload = {
            'report_reasons': ['Formatting of text'],
            'additional_details': 'Original details.',
        }
        create_response = self.client.post(self.base_url, create_payload, format='json')
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)

        report_public_id = create_response.data['public_id']
        detail_url = f'{self.base_url}{report_public_id}/'
        patch_payload = {
            'report_reasons': ['Solution incorrect or confusing', 'Other'],
        }
        patch_response = self.client.patch(detail_url, patch_payload, format='json')

        self.assertEqual(patch_response.status_code, status.HTTP_200_OK)
        self.assertCountEqual(
            patch_response.data['report_reasons'],
            ['Solution incorrect or confusing', 'Other'],
        )
