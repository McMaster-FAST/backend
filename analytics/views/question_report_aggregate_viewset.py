from analytics.models import QuestionReport, QuestionReportReason
from analytics.serializers import QuestionReportAggregateSerializer
from core.serializers.question_serializer import QuestionSerializer
from courses.serializers import UnitSerializer, UnitSubtopicSerializer
from django.db.models import Count
from core.models import Question
from courses.models import Course
from rest_framework import viewsets
from rest_framework.response import Response


class QuestionReportAggregateViewSet(viewsets.ViewSet):
    serializer_class = QuestionReportAggregateSerializer

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        course = Course.objects.filter(code=course_code).first()
        return (
            QuestionReport.objects.filter(question__subtopic__unit__course=course)
            if course
            else QuestionReport.objects.none()
        )

    def list(self, request, *args, **kwargs):
        # Generate a count of all the report types for this question
        questions = Question.objects.select_related("subtopic__unit").filter(
            subtopic__unit__course__code=self.kwargs.get("course_code")
        )

        counts = (
            QuestionReportReason.objects.filter(question_report__question__in=questions)
            .values("question_report__question__public_id", "reason")
            .annotate(count=Count("id"))
        )
        # We can have multile values for choices, so pick the first.
        reason_keys = [
            choice[0] for choice in QuestionReportReason.ReportReasonChoices.choices
        ]

        data = [
            {
                "question": QuestionSerializer(q).data,
                "unit": UnitSerializer(q.subtopic.unit).data,
                "subtopic": UnitSubtopicSerializer(q.subtopic).data,
                "reason_counts": {reason: 0 for reason in reason_keys},
            }
            for q in questions
        ]
        # Populate the reason counts
        question_items_by_id = {str(item["question"]["public_id"]): item for item in data}

        for row in counts:
            qid = str(row["question_report__question__public_id"])
            question_item = question_items_by_id.get(qid)
            if question_item:
                question_item["reason_counts"][row["reason"]] = row["count"]

        return Response(data)
