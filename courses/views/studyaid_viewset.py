from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import StudyAid, UnitSubtopic
from ..serializers import StudyAidSerializer


class StudyAidViewSet(viewsets.ModelViewSet):
    serializer_class = StudyAidSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter by the 'subtopic_pk' from the URL
        return StudyAid.objects.filter(subtopic=self.kwargs["subtopic_pk"])

    def perform_create(self, serializer):
        subtopic = UnitSubtopic.objects.get(pk=self.kwargs["subtopic_pk"])
        serializer.save(subtopic=subtopic)
