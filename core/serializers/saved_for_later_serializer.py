from rest_framework import serializers
from ..models import Question, SavedForLater


class SavedForLaterSerializer(serializers.ModelSerializer):
    question = serializers.SlugRelatedField(
        slug_field="public_id", queryset=Question.objects.all()
    )

    class Meta:
        model = SavedForLater
        fields = ["public_id", "question", "timestamp"]
        read_only_fields = ["public_id"]
