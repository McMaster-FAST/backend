from core.models import AdaptiveTestQuestionMetric
from rest_framework import serializers

class AdaptiveTestQuestionMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdaptiveTestQuestionMetric
        fields = []