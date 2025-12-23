from rest_framework import serializers
from core.models import Question
from courses.models import UnitSubtopic
from .question_image_serializer import QuestionImageSerializer
from .question_option_serializer import QuestionOptionSerializer


class QuestionSerializer(serializers.ModelSerializer):
    images = QuestionImageSerializer(many=True, read_only=True)

    options = QuestionOptionSerializer(
        many=True, read_only=True, source="questionoption_set"
    )

    subtopic = serializers.PrimaryKeyRelatedField(
        queryset=UnitSubtopic.objects.all(),
        required=False,  # <--- Crucial: Allows ViewSet to inject it later
        write_only=True,  # Don't show the ID in the output (redundant)
    )

    class Meta:
        model = Question
        fields = [
            "public_id",  # Crucial for frontend logic
            "serial_number",
            "content",
            "difficulty",
            "is_flagged",
            "is_active",
            "is_verified",
            "images",  # The images attached to the question
            "options",  # The multiple choice answers
            "subtopic",  # For assigning question to subtopic on creation
        ]
