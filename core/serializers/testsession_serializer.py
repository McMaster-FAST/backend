from rest_framework import serializers


class TestSessionSerializer(serializers.Serializer):
    subtopic_name = serializers.CharField(source="subtopic.name", read_only=True)
    unit_name = serializers.CharField(source="subtopic.unit.name", read_only=True)
    course_code = serializers.CharField(
        source="subtopic.unit.course.code", read_only=True
    )
