from core.serializers.saved_question_serializer import SavedQuestionSerializer
from rest_framework import serializers
from ..models import SavedForLater

class SavedForLaterSerializer(serializers.ModelSerializer):
    question = SavedQuestionSerializer(read_only=True)
    class Meta:
        model = SavedForLater
        fields = ["public_id", "question", "timestamp"]
        read_only_fields = ["public_id"]
