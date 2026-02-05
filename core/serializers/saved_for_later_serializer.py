from rest_framework import serializers
from ..models import SavedForLater

class SavedForLaterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedForLater
        fields = ["public_id", "question", "timestamp"]
        read_only_fields = ["public_id"]