from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.models import Question, QuestionOption
from core.serializers import QuestionOptionSerializer


class OptionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionOptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        question_uuid = self.kwargs.get("question_public_id")

        return QuestionOption.objects.filter(question__public_id=question_uuid)

    def perform_create(self, serializer):
        question_uuid = self.kwargs.get("question_public_id")
        question = Question.objects.get(public_id=question_uuid)
        serializer.save(question=question)
