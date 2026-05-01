from courses.models import QuestionUploadFailures, QuestionUploadResult
from rest_framework import serializers


class QuestionUploadFailureSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionUploadFailures
        fields = ["question_identifier", "error_message"]


class CourseUploadResultSerializer(serializers.ModelSerializer):
    failures = serializers.SerializerMethodField()

    class Meta:
        model = QuestionUploadResult
        fields = [
            "public_id",
            "result",
            "success_count",
            "failure_count",
            "progress",
            "failures",
        ]

    def get_failures(self, obj):
        return QuestionUploadFailureSerializer(obj.failures.all(), many=True).data
