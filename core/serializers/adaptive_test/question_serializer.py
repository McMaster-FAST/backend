from rest_framework import serializers
from .question_option_serializer import AdaptiveTestOptionSerializer

class AdaptiveTestQuestionSerializer(serializers.Serializer):
    content = serializers.CharField(source="question.content")
    options = AdaptiveTestOptionSerializer(many=True)
