from rest_framework import serializers
from core.models import QuestionOption


class QuestionOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = [
            "public_id",
            "content",
            "is_answer",
        ]
