from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from courses.models import StudyAid, UnitSubtopic
from courses.serializers import StudyAidSerializer


class StudyAidViewSet(viewsets.ModelViewSet):
    serializer_class = StudyAidSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"

    def _get_subtopic_public_id(self):
        return self.kwargs.get("subtopic_public_id") or self.kwargs.get("subtopic_pk")

    def get_queryset(self):
        queryset = StudyAid.objects.all()

        subtopic_public_id = self._get_subtopic_public_id()

        if subtopic_public_id:
            queryset = queryset.filter(subtopic__public_id=subtopic_public_id)

        return queryset

    def perform_create(self, serializer):
        subtopic_public_id = self._get_subtopic_public_id()

        if subtopic_public_id:
            subtopic = get_object_or_404(UnitSubtopic, public_id=subtopic_public_id)
            serializer.save(subtopic=subtopic)
        else:
            serializer.save()
