from rest_framework import serializers

class CourseIdentifierSerializer(serializers.Serializer):
    code = serializers.CharField()
    year = serializers.IntegerField()
    semester = serializers.CharField()

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    course = CourseIdentifierSerializer(write_only=True)
    create_required = serializers.BooleanField(default=False, write_only=True)
    
    def validate(self, attrs):
        # Could add custom validation in the future
        return super().validate(attrs)
    