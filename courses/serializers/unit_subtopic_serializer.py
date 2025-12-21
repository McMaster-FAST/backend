from rest_framework import serializers

from .subtopic_serializer import UnitSubtopicSerializer
from courses.models import Unit


class UnitDetailSerializer(serializers.ModelSerializer):
    """Used when viewing a single unit: Shows its Subtopics"""

    subtopics = UnitSubtopicSerializer(
        many=True, read_only=True, source="unitsubtopic_set"
    )

    class Meta:
        model = Unit
        fields = ["id", "number", "name", "description", "course", "subtopics"]
