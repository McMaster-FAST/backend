from rest_framework import serializers

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    group_name = serializers.CharField(required=False, allow_blank=False)

    def validate(self, attrs):
        # Could add custom validation in the future
        return super().validate(attrs)
    