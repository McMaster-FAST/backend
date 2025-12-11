from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import StudyAid
from ..serializers import StudyAidSerializer


class StudyAidViewSet(viewsets.ModelViewSet):
    queryset = StudyAid.objects.all()
    serializer_class = StudyAidSerializer
    permission_classes = [IsAuthenticated]
