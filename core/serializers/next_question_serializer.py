from rest_framework import serializers

from .question_image_serializer import QuestionImageSerializer
from .adaptive_test_option_serializer import AdaptiveTestOptionSerializer


class NextQuestionSerializer(serializers.Serializer):
    course_code = serializers.CharField(
        write_only=True, required=True, allow_blank=False
    )
    unit_name = serializers.CharField(write_only=True, required=True, allow_blank=False)
    subtopic_name = serializers.CharField(
        write_only=True, required=True, allow_blank=False
    )

    public_id = serializers.CharField(
        source="question.public_id", read_only=True
    )
    content = serializers.CharField(source="question.content", read_only=True)
    options = AdaptiveTestOptionSerializer(many=True, read_only=True)
