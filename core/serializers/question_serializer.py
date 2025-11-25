from ..models import Question
from rest_framework import serializers
from .question_image_serializer import QuestionImageSerializer

class QuestionSerializer(serializers.ModelSerializer):
    images = QuestionImageSerializer(many=True, read_only=True)
    class Meta:
        model = Question
        fields = [
            'content', 'difficulty', "serial_number", "content", "difficulty", "is_flagged", 
            "is_active", "is_verified", "images" 
        ]