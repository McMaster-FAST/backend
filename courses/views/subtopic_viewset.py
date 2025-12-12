from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import UnitSubtopic, Unit
from ..serializers import UnitSubtopicSerializer


class SubtopicViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSubtopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Filter by the 'unit_pk' from the URL
        return UnitSubtopic.objects.filter(unit=self.kwargs["unit_pk"])

    def perform_create(self, serializer):
        unit = Unit.objects.get(pk=self.kwargs["unit_pk"])
        serializer.save(unit=unit)
