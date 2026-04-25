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
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = UnitSubtopic
        exclude = ["id"]

    def get_user_ability(self, obj):
        scores = getattr(obj, "prefetched_scores", [])

        if scores:
            return UserTopicAbilityScoreSerializer(scores[0]).data

        # Return model defaults if no score exists yet
        return None

    def get_question_count(self, obj):
        # Prefer annotated count from queryset; fallback keeps compatibility.
        if hasattr(obj, "question_count"):
            return obj.question_count
        return obj.question_set.filter(is_active=True).count()
