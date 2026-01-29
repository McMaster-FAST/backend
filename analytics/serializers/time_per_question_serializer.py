from rest_framework import serializers


class TimePerQuestionRequestSerializer(serializers.Serializer):
    course_id = serializers.IntegerField(required=True)


class QuestionTimeStatisticsSerializer(serializers.Serializer):

    unit_id = serializers.IntegerField()
    unit_name = serializers.CharField()
    unit_number = serializers.IntegerField()
    subtopic_id = serializers.IntegerField()
    subtopic_name = serializers.CharField()
    question_id = serializers.IntegerField()
    question_serial_number = serializers.CharField()
    average_time_spent = serializers.FloatField()
    total_attempts = serializers.IntegerField()
    unique_students = serializers.IntegerField()


class TimePerQuestionResponseSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    statistics = QuestionTimeStatisticsSerializer(many=True)
