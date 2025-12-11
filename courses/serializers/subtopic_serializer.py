from rest_framework import serializers

from .studyaid_serializer import StudyAidSerializer
from ..models import UnitSubtopic


class UnitSubtopicSerializer(serializers.ModelSerializer):
    # Study Aids inside Subtopics
    study_aids = StudyAidSerializer(many=True, read_only=True, source="studyaid_set")

    class Meta:
        model = UnitSubtopic
        fields = ["id", "name", "description", "unit", "study_aids"]
