from rest_framework import serializers
from courses.models import Course

from .unit_subtopic_serializer import UnitDetailSerializer


class CourseDetailSerializer(serializers.ModelSerializer):
    units = UnitDetailSerializer(many=True, read_only=True, source="unit_set")

    class Meta:
        model = Course
        fields = [
            "id",
            "name",
            "code",
            "description",
            "year",
            "semester",
            "is_archived",
            "units",
        ]
