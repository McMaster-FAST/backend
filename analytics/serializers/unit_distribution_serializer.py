from rest_framework import serializers


class UnitDistributionRequestSerializer(serializers.Serializer):
    course_public_id = serializers.UUIDField(required=True)


class UnitStatisticsSerializer(serializers.Serializer):

    user_id = serializers.IntegerField()
    unit_id = serializers.IntegerField()
    unit_name = serializers.CharField()
    unit_number = serializers.IntegerField()
    total_attempts = serializers.IntegerField()
    questions_attempted = serializers.IntegerField()


class UnitDistributionResponseSerializer(serializers.Serializer):
    course_public_id = serializers.UUIDField()
    statistics = UnitStatisticsSerializer(many=True)
