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
        if Path(attrs["file"].name).suffix.lower() not in [
            f".{ext}" for ext in self.supported_formats
        ]:
            raise serializers.ValidationError(
                f"Unsupported file format. Supported formats are: {', '.join(self.supported_formats)}"
            )
        return super().validate(attrs)

