from rest_framework import serializers
from core.models import TestSession
from core.serializers.question_serializer import QuestionSerializer


class QuestionIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionSerializer.Meta.model
        fields = ["public_id"]


class TestSessionSerializer(serializers.ModelSerializer):
    # Read-only fields for nested data
    subtopic_name = serializers.CharField(source="subtopic.name", read_only=True)
    current_question_id = QuestionIDSerializer(read_only=True)
    excluded_questions = QuestionIDSerializer(many=True, read_only=True)

    class Meta:
        model = TestSession
        fields = [
            "subtopic_name",
            "current_question_id",
            "excluded_questions",
            "use_out_of_range_questions",
        ]


class TestSessionWriteSerializer(serializers.ModelSerializer):
    """Serializer for write operations - only allows specific fields"""

    class Meta:
        model = TestSession
        fields = ["excluded_questions", "use_out_of_range_questions"]
