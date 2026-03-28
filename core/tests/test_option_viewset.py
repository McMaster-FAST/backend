import uuid

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from core.models import Question
from core.models import QuestionOption

pytestmark = pytest.mark.django_db


def _options_url(question: Question) -> str:
    return f'/api/questions/{question.public_id}/options/'


def _option_detail_url(question: Question, option: QuestionOption) -> str:
    return f'/api/questions/{question.public_id}/options/{option.public_id}/'


class TestListOptions:
    def test_returns_options_for_question(
        self,
        api_client: APIClient,
        question: Question,
        question_option: QuestionOption,
    ) -> None:
        response = api_client.get(_options_url(question))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['public_id'] == str(question_option.public_id)
        assert response.data[0]['content'] == '4'

    def test_returns_empty_for_question_with_no_options(
        self,
        api_client: APIClient,
        question: Question,
    ) -> None:
        response = api_client.get(_options_url(question))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_unauthenticated_returns_401(
        self,
        unauthenticated_client: APIClient,
        question: Question,
    ) -> None:
        response = unauthenticated_client.get(_options_url(question))

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )


class TestCreateOption:
    def test_with_valid_data_returns_201(
        self,
        api_client: APIClient,
        question: Question,
    ) -> None:
        data = {'content': 'Option A', 'is_answer': False}
        response = api_client.post(_options_url(question), data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['content'] == 'Option A'
        assert response.data['is_answer'] is False
        assert 'public_id' in response.data

    def test_with_missing_content_returns_400(
        self,
        api_client: APIClient,
        question: Question,
    ) -> None:
        data = {'is_answer': True}
        response = api_client.post(_options_url(question), data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_for_nonexistent_question_returns_404(
        self,
        api_client: APIClient,
    ) -> None:
        fake_uuid = uuid.uuid4()
        url = f'/api/questions/{fake_uuid}/options/'
        data = {'content': 'Option A', 'is_answer': False}

        response = api_client.post(url, data)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_returns_401(
        self,
        unauthenticated_client: APIClient,
        question: Question,
    ) -> None:
        data = {'content': 'Option A', 'is_answer': False}
        response = unauthenticated_client.post(
            _options_url(question), data
        )

        assert response.status_code in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_public_id_is_read_only(
        self,
        api_client: APIClient,
        question: Question,
    ) -> None:
        fake_uuid = str(uuid.uuid4())
        data = {
            'content': 'Option A',
            'is_answer': False,
            'public_id': fake_uuid,
        }
        response = api_client.post(_options_url(question), data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['public_id'] != fake_uuid

    def test_selection_frequency_is_read_only(
        self,
        api_client: APIClient,
        question: Question,
    ) -> None:
        data = {
            'content': 'Option A',
            'is_answer': False,
            'selection_frequency': '0.9999',
        }
        response = api_client.post(_options_url(question), data)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['selection_frequency'] == '0.0000'


class TestRetrieveOption:
    def test_returns_200(
        self,
        api_client: APIClient,
        question: Question,
        question_option: QuestionOption,
    ) -> None:
        response = api_client.get(
            _option_detail_url(question, question_option)
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['public_id'] == str(question_option.public_id)
        assert response.data['content'] == '4'
        assert response.data['is_answer'] is True
        assert 'selection_frequency' in response.data
        assert 'images' in response.data

    def test_nonexistent_option_returns_404(
        self,
        api_client: APIClient,
        question: Question,
    ) -> None:
        fake_uuid = uuid.uuid4()
        url = f'/api/questions/{question.public_id}/options/{fake_uuid}/'

        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestUpdateOption:
    def test_full_update_returns_200(
        self,
        api_client: APIClient,
        question: Question,
        question_option: QuestionOption,
    ) -> None:
        data = {'content': 'Updated content', 'is_answer': False}
        response = api_client.put(
            _option_detail_url(question, question_option),
            data,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['content'] == 'Updated content'
        assert response.data['is_answer'] is False

    def test_partial_update_returns_200(
        self,
        api_client: APIClient,
        question: Question,
        question_option: QuestionOption,
    ) -> None:
        data = {'content': 'Partially updated'}
        response = api_client.patch(
            _option_detail_url(question, question_option),
            data,
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['content'] == 'Partially updated'
        assert response.data['is_answer'] is True


class TestDeleteOption:
    def test_returns_204(
        self,
        api_client: APIClient,
        question: Question,
        question_option: QuestionOption,
    ) -> None:
        response = api_client.delete(
            _option_detail_url(question, question_option)
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not QuestionOption.objects.filter(
            public_id=question_option.public_id
        ).exists()

    def test_nonexistent_option_returns_404(
        self,
        api_client: APIClient,
        question: Question,
    ) -> None:
        fake_uuid = uuid.uuid4()
        url = f'/api/questions/{question.public_id}/options/{fake_uuid}/'

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND
