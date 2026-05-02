
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from courses.models import UnitSubtopic, Unit
from courses.serializers import UnitSubtopicSerializer


class SubtopicViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSubtopicSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "public_id"

    def _get_unit_public_id(self):
        return self.kwargs.get("unit_public_id") or self.kwargs.get("unit_pk")

    def get_queryset(self):
        queryset = UnitSubtopic.objects.all()

        unit_public_id = self._get_unit_public_id()

        if unit_public_id:
            queryset = queryset.filter(unit__public_id=unit_public_id)

        return queryset

    def perform_create(self, serializer):
        unit_public_id = self._get_unit_public_id()

        if unit_public_id:
            unit = get_object_or_404(Unit, public_id=unit_public_id)
            serializer.save(unit=unit)
        else:
            serializer.save()
