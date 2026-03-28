# analytics/serializers.py
from rest_framework import serializers
from analytics.models import CourseXP


class CourseXPSerializer(serializers.ModelSerializer):
    # Explicitly declare properties to include them in the JSON response
    level = serializers.IntegerField(read_only=True)
    xp_in_current_level = serializers.IntegerField(read_only=True)
    xp_for_next_level = serializers.IntegerField(read_only=True)
    progress_percentage = serializers.IntegerField(read_only=True)

    class Meta:
        model = CourseXP
        fields = [
            "course",
            "total_xp",
            "level",
            "xp_in_current_level",
            "xp_for_next_level",
            "progress_percentage",
        ]
