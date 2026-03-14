from analytics.models import QuestionReportReason
from rest_framework import serializers


class QuestionReportAggregateSerializer(serializers.Serializer):
    reason = serializers.ChoiceField(
        choices=QuestionReportReason.ReportReasonChoices.choices
    )
    count = serializers.IntegerField()
