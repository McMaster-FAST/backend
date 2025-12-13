from rest_framework import serializers
from core.models import QuestionImage


class QuestionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionImage
        fields = ["image_file", "alt_text"]
