from core.models import CourseResumeState
from analytics.models import QuestionAttempt
from core.models import Question
from core.serializers.resume_serializer import ResumeTargetSerializer
from courses.serializers.subtopic_serializer import UnitSubtopicSerializer
from rest_framework import serializers
from courses.models import Course


class CourseSerializer(serializers.ModelSerializer):
    resume_target = serializers.SerializerMethodField()
    correct_questions = serializers.SerializerMethodField()
    total_questions = serializers.SerializerMethodField()

    def get_resume_target(self, obj):
        resume_state = CourseResumeState.objects.filter(
            course__public_id=obj.public_id, user=self.context["request"].user
        ).first()
        if resume_state:
            return ResumeTargetSerializer(
                {
                    "course_code": resume_state.last_subtopic.unit.course.code,
                    "unit_name": resume_state.last_subtopic.unit.name,
                    "subtopic_name": resume_state.last_subtopic.name,
                }
            ).data
        return None

    def get_correct_questions(self, obj):
        request = self.context.get("request")
        if not request:
            return 0
        return (
            QuestionAttempt.objects.filter(
                user=request.user,
                question__subtopic__unit__course=obj,
                question__is_active=True,
                answered_correctly=True,
                skipped=False,
            )
            .values("question_id")
            .distinct()
            .count()
        )

    def get_total_questions(self, obj):
        return Question.objects.filter(
            subtopic__unit__course=obj,
            is_active=True,
        ).count()

    class Meta:
        model = Course
        exclude = ["id"]
