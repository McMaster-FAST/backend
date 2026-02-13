from rest_framework import serializers

from .studyaid_serializer import StudyAidSerializer
from courses.models import UnitSubtopic


class UnitSubtopicSerializer(serializers.ModelSerializer):
    # Study Aids inside Subtopics
    study_aids = StudyAidSerializer(many=True, read_only=True, source="studyaid_set")

    class Meta:
        model = UnitSubtopic
        exclude = ["id"]
