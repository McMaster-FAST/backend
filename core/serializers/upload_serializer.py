from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    course_code = serializers.CharField(write_only=True)
    course_year = serializers.IntegerField(write_only=True)
    course_semester = serializers.CharField(write_only=True)
    create_required = serializers.BooleanField(default=False, write_only=True)
    
    def validate(self, attrs):
        # Could add custom validation in the future
        return super().validate(attrs)
    