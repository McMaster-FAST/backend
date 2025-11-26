from rest_framework import serializers
from ..models import QuestionOption
from ..serializers.question_image_serializer import QuestionImageSerializer

class AdaptiveTestOptionSerializer(serializers.ModelSerializer):
    images = QuestionImageSerializer(many=True)
    class Meta:
        model = QuestionOption
        fields = ["public_id", "content", "images"]