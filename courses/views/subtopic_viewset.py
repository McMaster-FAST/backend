from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import UnitSubtopic
from ..serializers import UnitSubtopicSerializer


class SubtopicViewSet(viewsets.ModelViewSet):
    queryset = UnitSubtopic.objects.all()
    serializer_class = UnitSubtopicSerializer
    permission_classes = [IsAuthenticated]
