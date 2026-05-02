from rest_framework import serializers

from analytics.models import QuestionAttempt
from core.models import Question
from .subtopic_serializer import UnitSubtopicSerializer
from courses.models import Unit


class UnitDetailSerializer(serializers.ModelSerializer):
    """Used when viewing a single unit: Shows its Subtopics"""

    subtopics = UnitSubtopicSerializer(
        many=True, read_only=True, source="unitsubtopic_set"
    )
    correct_questions = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Unit
        fields = [
            "public_id",
            "number",
            "name",
            "description",
            "course",
            "correct_questions",
            "total_questions",
            "completion_percentage",
            "subtopics",
        ]

    def get_correct_questions(self, obj):
        request = self.context.get("request")
        if not request:
            return 0

        return (
            QuestionAttempt.objects.filter(
                user=request.user,
                question__subtopic__unit=obj,
                question__is_active=True,
                answered_correctly=True,
                skipped=False,
            )
            .values("question_id")
            .distinct()
            .count()
        )

    def get_total_questions(self, obj):
        prefetched_subtopics = getattr(obj, "_prefetched_objects_cache", {}).get(
            "unitsubtopic_set"
        )
        if prefetched_subtopics is not None:
            return sum(
                subtopic.question_count
                if hasattr(subtopic, "question_count")
                else subtopic.question_set.filter(is_active=True).count()
                for subtopic in prefetched_subtopics
            )

        return Question.objects.filter(subtopic__unit=obj, is_active=True).count()

    def get_completion_percentage(self, obj):
        total_questions = self.get_total_questions(obj)
        if not total_questions:
            return 0.0

        return round((self.get_correct_questions(obj) / total_questions) * 100, 2)
