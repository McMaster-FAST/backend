from analytics.models import QuestionReport
from analytics.serializers import QuestionReportSerializer
from core.models import Question
from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError


class QuestionReportViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionReportSerializer
    lookup_field = 'public_id'

    def get_queryset(self):
        queryset = (
            QuestionReport.objects.select_related('question', 'user')
            .prefetch_related('report_reasons')
            .order_by('-timestamp')
        )

        question_uuid = self.kwargs.get('question_public_id')
        if question_uuid:
            queryset = queryset.filter(question__public_id=question_uuid)

        return queryset

    def perform_create(self, serializer):
        question_uuid = self.kwargs.get('question_public_id')
        if not question_uuid:
            raise ValidationError(
                detail="You must POST to a question's report endpoint."
            )

        try:
            question = Question.objects.get(public_id=question_uuid)
        except Question.DoesNotExist:
            raise NotFound(detail='The specified question does not exist.')

        serializer.save(question=question)
