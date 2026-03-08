from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated

from django_filters.rest_framework import DjangoFilterBackend

from ..models import Question
from ..serializers import QuestionSerializer
from courses.models import UnitSubtopic


class QuestionViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"  # As discussed for UUIDs

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]

    filterset_fields = {
        "is_verified": ["exact"],  # allows ?is_verified=true
        "is_flagged": ["exact"],  # allows ?is_flagged=true
        "subtopic__name": ["icontains"],
        "difficulty": [
            "gte",
            "lte",
        ],
    }

    search_fields = [
        "content",
    ]

    def get_queryset(self):
        queryset = Question.objects.all()

        subtopic_pk = self.kwargs.get("subtopic_pk")
        if subtopic_pk:
            queryset = queryset.filter(subtopic_id=subtopic_pk)

        course_code = self.kwargs.get("course_code")
        if course_code:
            queryset = queryset.filter(subtopic__unit__course__code=course_code)

        return queryset

    def perform_create(self, serializer):
        subtopic_pk = self.kwargs.get("subtopic_pk")

        if subtopic_pk:
            subtopic = UnitSubtopic.objects.get(pk=subtopic_pk)
            serializer.save(subtopic=subtopic)
        else:
            serializer.save()
