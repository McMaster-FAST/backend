from core.models import Question
from core.serializers.instructor_question_serializer import QuestionSerializer
from rest_framework import serializers


class QuestionReportAggregateSerializer(serializers.ModelSerializer):
    unit_name = serializers.CharField(source="subtopic.unit.name")
    subtopic_name = serializers.CharField(source="subtopic.name")
    total_reports = serializers.IntegerField()

    class Meta:
        model = Question
        fields = ["public_id", "content", "unit_name", "subtopic_name", "total_reports"]
