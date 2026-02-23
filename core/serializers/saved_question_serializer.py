from rest_framework import serializers
from ..models import Question

class SavedQuestionSerializer(serializers.ModelSerializer):
    """
    A minimal serializer
    """
    subtopic_name = serializers.CharField(source="subtopic.name", read_only=True)
    unit_name = serializers.CharField(source="subtopic.unit.name", read_only=True)
    course_name = serializers.CharField(source="subtopic.unit.course.name", read_only=True)
    class Meta:
        model = Question
        fields = ["public_id", "content", "subtopic_name", "unit_name", "course_name"]