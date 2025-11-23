from rest_framework import serializers


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    course = serializers.JSONField()
    
    def validate(self, attrs):
        # Could add custom validation in the future
        return super().validate(attrs)
    