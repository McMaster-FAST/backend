from rest_framework import serializers
from ..models import QuestionImage

class QuestionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionImage
        fields = "__all__"