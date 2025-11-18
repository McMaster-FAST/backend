from rest_framework import serializers
from .question_image_serializer import QuestionImageSerializer
from .adaptive_test_option_serializer import AdaptiveTestOptionSerializer

class AdaptiveTestQuestionBundle:
    def __init__(self, question, options):
        self.question = question
        self.options = options

class AdaptiveTestQuestionSerializer(serializers.Serializer):
    serial_number = serializers.CharField(source="question.serial_number")
    content = serializers.CharField(source="question.content")
    images = QuestionImageSerializer(source="question.images", many=True)
    options = AdaptiveTestOptionSerializer(many=True)
