from courses.models import Enrolment
from rest_framework import serializers
from pathlib import Path


class FileUploadSerializer(serializers.Serializer):
    supported_formats = ["docx", "xlsx", "csv"]
    file = serializers.FileField(write_only=True)
    course_code = serializers.CharField(write_only=True)
    course_year = serializers.IntegerField(write_only=True)
    course_semester = serializers.CharField(write_only=True)
    create_required = serializers.BooleanField(default=False, write_only=True)

    def validate(self, attrs):
        if not self._user_has_permission(self.context["request"].user):
            raise serializers.ValidationError(
                "You do not have permission to upload files for this course."
            )
        if Path(attrs["file"].name).suffix.lower() not in [
            f".{ext}" for ext in self.supported_formats
        ]:
            raise serializers.ValidationError(
                f"Unsupported file format. Supported formats are: {', '.join(self.supported_formats)}"
            )
        return super().validate(attrs)

    def _user_has_permission(self, user):
        user_enrolment = Enrolment.objects.filter(
            user=user,
            course__code=self.context.get("course_code"),
            course__year=self.context.get("course_year"),
            course__semester=self.context.get("course_semester"),
        )
        if not user_enrolment.exists():
            return False
        return user_enrolment.first().is_instructor or user_enrolment.first().is_ta
