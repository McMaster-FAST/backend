from rest_framework import serializers
from analytics.models import UserTopicAbilityScore


class UserTopicAbilityScoreSerializer(serializers.ModelSerializer):
    mastery_caption = serializers.SerializerMethodField()
    mastery_value = serializers.SerializerMethodField()

    class Meta:
        model = UserTopicAbilityScore
        fields = ["mastery_caption", "mastery_value"]

    def _get_mastery_data(self, score):
        """Single source of truth for mapping IRT scores to discrete UI percentage tranches."""
        if score < -1.0:
            return {"value": 20, "caption": "Novice"}
        elif score < -0.25:
            return {"value": 40, "caption": "Developing"}
        elif score < 0.25:
            return {"value": 60, "caption": "Average"}
        elif score < 1.0:
            return {"value": 80, "caption": "Advanced"}
        else:
            return {"value": 100, "caption": "Proficient"}

    def get_mastery_caption(self, obj):
        return self._get_mastery_data(float(obj.score))["caption"]

    def get_mastery_value(self, obj):
        return self._get_mastery_data(float(obj.score))["value"]
