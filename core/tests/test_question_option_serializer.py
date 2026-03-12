import pytest

from core.models import Question
from core.models import QuestionOption
from core.serializers.question_option_serializer import QuestionOptionSerializer

pytestmark = pytest.mark.django_db


class TestQuestionOptionSerializer:
    def test_contains_expected_fields(
        self,
        question_option: QuestionOption,
    ) -> None:
        serializer = QuestionOptionSerializer(question_option)
        expected_fields = {
            'public_id',
            'content',
            'is_answer',
            'selection_frequency',
            'images',
        }

        assert set(serializer.data.keys()) == expected_fields

    def test_read_only_fields(self) -> None:
        meta = QuestionOptionSerializer.Meta
        assert 'public_id' in meta.read_only_fields
        assert 'selection_frequency' in meta.read_only_fields

    def test_valid_data(
        self,
        question: Question,
    ) -> None:
        data = {'content': 'Test option', 'is_answer': True}
        serializer = QuestionOptionSerializer(data=data)

        assert serializer.is_valid()

    def test_invalid_missing_content(self) -> None:
        data = {'is_answer': True}
        serializer = QuestionOptionSerializer(data=data)

        assert not serializer.is_valid()
        assert 'content' in serializer.errors

    def test_images_field_returns_empty_list_by_default(
        self,
        question_option: QuestionOption,
    ) -> None:
        serializer = QuestionOptionSerializer(question_option)

        assert serializer.data['images'] == []
