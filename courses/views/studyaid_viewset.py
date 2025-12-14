from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import StudyAid, UnitSubtopic
from ..serializers import StudyAidSerializer


class StudyAidViewSet(viewsets.ModelViewSet):
    serializer_class = StudyAidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = StudyAid.objects.all()

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
