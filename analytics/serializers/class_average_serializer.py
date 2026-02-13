from rest_framework import serializers


class ClassAverageRequestSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(required=True)


class SubtopicStatisticsSerializer(serializers.Serializer):

    unit_id = serializers.IntegerField()
    unit_name = serializers.CharField()
    unit_number = serializers.IntegerField()
    subtopic_id = serializers.IntegerField()
    subtopic_name = serializers.CharField()
    average_score = serializers.FloatField()
    total_attempts = serializers.IntegerField()
    unique_students = serializers.IntegerField()


class ClassAverageResponseSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    statistics = SubtopicStatisticsSerializer(many=True)
