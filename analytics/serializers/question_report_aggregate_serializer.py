from courses.serializers import UnitSerializer
from courses.serializers import UnitSubtopicSerializer
from rest_framework import serializers


class QuestionReportAggregateSerializer(serializers.Serializer):
    question_public_id = serializers.UUIDField()
    unit = UnitSerializer()
    subtopic = UnitSubtopicSerializer()
    reason_counts = serializers.DictField(child=serializers.IntegerField())