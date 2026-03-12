from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from core.models import Question
from core.models import QuestionOption
from core.serializers import QuestionOptionSerializer


class OptionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionOptionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'public_id'

    def get_queryset(self) -> QuerySet[QuestionOption]:
        question_uuid: str | None = self.kwargs.get('question_public_id')
        return QuestionOption.objects.filter(
            question__public_id=question_uuid
        )

    def perform_create(self, serializer: QuestionOptionSerializer) -> None:
        question_uuid: str | None = self.kwargs.get('question_public_id')

        if question_uuid:
            try:
                question = Question.objects.get(public_id=question_uuid)
                serializer.save(question=question)
            except Question.DoesNotExist:
                raise NotFound(
                    detail='The specified question does not exist.'
                ) from None
        else:
            raise ValidationError(
                detail="You must POST to a question's option endpoint."
            )
