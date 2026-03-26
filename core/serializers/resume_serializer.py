from rest_framework import serializers


class ResumeTargetSerializer(serializers.Serializer):
    course_code = serializers.CharField()
    unit_name = serializers.CharField()
    subtopic_name = serializers.CharField()

