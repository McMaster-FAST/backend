from rest_framework import serializers

from analytics.serializers.ability_score_serializer import (
    UserTopicAbilityScoreSerializer,
)

from .studyaid_serializer import StudyAidSerializer
from courses.models import UnitSubtopic


class UnitSubtopicSerializer(serializers.ModelSerializer):
    # Study Aids inside Subtopics
    study_aids = StudyAidSerializer(many=True, read_only=True, source="studyaid_set")
    user_ability = serializers.SerializerMethodField()

    class Meta:
        model = UnitSubtopic
        exclude = ["id"]

    def get_user_ability(self, obj):
        scores = getattr(obj, "prefetched_scores", [])

        print(scores)

        if scores:
            return UserTopicAbilityScoreSerializer(scores[0]).data

        # Return model defaults if no score exists yet
        return None
