from core.models import CourseResumeState
from core.serializers.resume_serializer import ResumeTargetSerializer
from courses.serializers.subtopic_serializer import UnitSubtopicSerializer
from rest_framework import serializers
from courses.models import Course


class CourseSerializer(serializers.ModelSerializer):
    resume_target = serializers.SerializerMethodField()

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

    class Meta:
        model = Course
        exclude = ["id"]
