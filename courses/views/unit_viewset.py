from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import Unit
from ..serializers import UnitSerializer, UnitDetailSerializer


class UnitViewSet(viewsets.ModelViewSet):
    queryset = Unit.objects.all()
    permission_classes = [IsAuthenticated]  # Add IsInstructor logic if needed

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UnitDetailSerializer  # Returns Unit -> Subtopics
        return UnitSerializer
