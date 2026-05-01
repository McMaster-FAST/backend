from rest_framework import serializers
from core.models import Question, SavedForLater
from courses.models import UnitSubtopic
from .question_image_serializer import QuestionImageSerializer
from .question_option_serializer import QuestionOptionSerializer


class QuestionSerializer(serializers.ModelSerializer):
    images = QuestionImageSerializer(many=True, read_only=True)

    options = QuestionOptionSerializer(
        many=True, read_only=True, source="questionoption_set"
    )

    subtopic = serializers.SlugRelatedField(
        queryset=UnitSubtopic.objects.all(),
        slug_field="public_id",
        required=False,
        write_only=True,  # Don't show the ID in the output (redundant)
    )

    subtopic_name = serializers.CharField(source="subtopic.name", read_only=True)
    subtopic_public_id = serializers.UUIDField(source="subtopic.public_id", read_only=True)
    unit_public_id = serializers.UUIDField(source="subtopic.unit.public_id", read_only=True)
    unit_name = serializers.CharField(source="subtopic.unit.name", read_only=True)
    saved_for_later = serializers.SerializerMethodField()

    def get_saved_for_later(self, obj):
        request = self.context.get("request")
        user = request.user if request else None
        if user:
            return SavedForLater.objects.filter(user=user, question__public_id=obj.public_id).exists()
        return False

    class Meta:
        model = Question
        fields = [
            "public_id",  # Crucial for frontend logic
            "serial_number",
            "content",
            "difficulty",
            "selection_frequency",
            "is_flagged",
            "is_active",
            "is_verified",
            "answer_explanation",
            "images",  # The images attached to the question
            "options",  # The multiple choice answers
            "subtopic",  # For assigning question to subtopic on creation
            "subtopic_public_id",
            "subtopic_name",
            "unit_public_id",
            "unit_name",
            "saved_for_later",
        ]
        read_only_fields = ["public_id", "selection_frequency"]
        extra_kwargs = {
            "content": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "Question content is required.",
                    "blank": "Question content is required.",
                },
            },
            "serial_number": {
                "required": True,
                "allow_blank": False,
                "error_messages": {
                    "required": "Serial number is required.",
                    "blank": "Serial number is required.",
                },
            },
            "difficulty": {
                "required": False,
                "min_value": -3,
                "max_value": 3,
                "error_messages": {
                    "min_value": "Difficulty must be at least -3.0000.",
                    "max_value": "Difficulty must be at most 3.0000.",
                },
            },
        }
