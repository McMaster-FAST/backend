from rest_framework import serializers
from ..models import Enrolment


class EnrolmentSerializer(serializers.ModelSerializer):
    course_code = serializers.CharField(source="course.code", read_only=True)
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Enrolment
        fields = [
            "id",
            "user",
            "user_name",
            "course",
            "course_code",
            "is_instructor",
            "is_ta",
        ]

    def validate(self, data):
        """
        - Admin: Can create for any course.
        - Instructor: Can create only for their courses.
        - Student/TA: Cannot create.
        """
        request = self.context.get("request")
        target_course = data.get("course")

        # Admin Override
        if request.user.is_staff:
            return data

        # Check if request.user is an Instructor for the target course
        is_instructor = Enrolment.objects.filter(
            user=request.user, course=target_course, is_instructor=True
        ).exists()

        if not is_instructor:
            raise serializers.ValidationError(
                "You must be an Instructor of this course to enroll students."
            )

        return data
