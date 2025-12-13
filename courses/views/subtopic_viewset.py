from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import UnitSubtopic, Unit
from ..serializers import UnitSubtopicSerializer


class SubtopicViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSubtopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = UnitSubtopic.objects.all()

        unit_pk = self.kwargs.get("unit_pk")

        if unit_pk:
            queryset = queryset.filter(unit=unit_pk)

        return queryset

    def perform_create(self, serializer):
        unit_pk = self.kwargs.get("unit_pk")

        if unit_pk:
            unit = Unit.objects.get(pk=unit_pk)
            serializer.save(unit=unit)
        else:
            serializer.save()
