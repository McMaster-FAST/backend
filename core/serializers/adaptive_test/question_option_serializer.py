from rest_framework import serializers
from ...models import QuestionOption

class AdaptiveTestOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ["public_id", "content"]