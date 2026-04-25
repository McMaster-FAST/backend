from courses.models import QuestionUploadResult
from rest_framework import serializers


class CourseUploadResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionUploadResult
        fields = [
            "public_id",
            "result",
            "success_count",
            "failure_count",
            "progress",
        ]
