from ..models import Question
from rest_framework import serializers

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'content', 'difficulty', "serial_number", "content", "difficulty", "is_flagged", 
            "is_active", "is_verified", "images" 
        ]