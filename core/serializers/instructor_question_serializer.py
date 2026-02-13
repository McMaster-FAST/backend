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

    subtopic = serializers.PrimaryKeyRelatedField(
        queryset=UnitSubtopic.objects.all(),
        required=False,
        write_only=True,  # Don't show the ID in the output (redundant)
    )

    subtopic_name = serializers.CharField(source="subtopic.name", read_only=True)
    saved_for_later = serializers.SerializerMethodField()

    def get_saved_for_later(self, obj):
        user = self.context.get("request").user
        print("USER:", user)
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
            "is_flagged",
            "is_active",
            "is_verified",
            "images",  # The images attached to the question
            "options",  # The multiple choice answers
            "subtopic",  # For assigning question to subtopic on creation
            "subtopic_name",
            "saved_for_later", 
        ]
