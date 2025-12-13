from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import Question
from ..serializers import QuestionSerializer
from courses.models import UnitSubtopic


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"  # As discussed for UUIDs

    def get_queryset(self):
        queryset = Question.objects.all()

        subtopic_pk = self.kwargs.get("subtopic_pk")
        if subtopic_pk:
            queryset = queryset.filter(subtopic_id=subtopic_pk)

        return queryset

    def perform_create(self, serializer):
        subtopic_pk = self.kwargs.get("subtopic_pk")

        if subtopic_pk:
            subtopic = UnitSubtopic.objects.get(pk=subtopic_pk)
            serializer.save(subtopic=subtopic)
        else:
            serializer.save()
