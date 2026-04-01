from uuid import UUID

from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from core.models import Question
from core.models import QuestionOption
from core.serializers import QuestionOptionCRUDSerializer


class OptionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionOptionCRUDSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'public_id'

    def _get_validated_question_uuid(self) -> UUID:
        raw_uuid: str | None = self.kwargs.get('question_public_id')
        if not raw_uuid:
            raise ValidationError(detail='You must specify a question.')
        try:
            return UUID(str(raw_uuid))
        except ValueError:
            raise NotFound(detail='The specified question does not exist.') from None

    def get_queryset(self) -> QuerySet[QuestionOption]:
        question_uuid: UUID = self._get_validated_question_uuid()
        return QuestionOption.objects.filter(question__public_id=question_uuid)

    def perform_create(self, serializer: QuestionOptionCRUDSerializer) -> None:
        question_uuid: UUID = self._get_validated_question_uuid()
        try:
            question = Question.objects.get(public_id=question_uuid)
        except Question.DoesNotExist:
            raise NotFound(detail='The specified question does not exist.') from None
        serializer.save(question=question)
