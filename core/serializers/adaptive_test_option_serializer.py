from rest_framework import serializers
from ..models import QuestionOption
from ..serializers.question_image_serializer import QuestionImageSerializer

class AdaptiveTestOptionSerializer(serializers.ModelSerializer):
    images = QuestionImageSerializer(many=True, required=False)
    class Meta:
        model = QuestionOption
        fields = ['id', 'content', 'images']