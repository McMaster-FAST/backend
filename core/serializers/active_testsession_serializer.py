from rest_framework import serializers
from core.models import TestSession, Question


class ActiveTestSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for the active test session with writable skipped_questions.
    """

    subtopic = serializers.UUIDField(source="subtopic.public_id", read_only=True)
    current_question = serializers.UUIDField(
        source="current_question.public_id", read_only=True
    )
    answered_questions = serializers.SlugRelatedField(
        many=True,
        slug_field="public_id",
        queryset=Question.objects.all(),
        required=False,
    )

    # Make skipped_questions writable by accepting public_id values
    skipped_questions = serializers.SlugRelatedField(
        many=True,
        slug_field="public_id",
        queryset=Question.objects.all(),
        required=False,
    )

    class Meta:
        model = TestSession
        fields = [
            "public_id",
            "subtopic",
            "difficulty_range",
            "current_question",
            "answered_questions",
            "skipped_questions",
        ]
        read_only_fields = [
            "public_id",
            "subtopic",
            "current_question",
            "answered_questions",
        ]

    def to_representation(self, instance):
        """
        Convert the output to use public_id for skipped_questions
        Idk what this is, but it works with it here
        """
        representation = super().to_representation(instance)
        # Convert skipped_questions to use QuestionPublicSerializer for output
        representation["skipped_questions"] = [
            question.public_id for question in instance.skipped_questions.all()
        ]
        return representation
