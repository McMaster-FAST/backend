from analytics.models import QuestionReport, QuestionReportReason
from analytics.serializers import QuestionReportAggregateSerializer
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.response import Response


class QuestionReportAggregateViewSet(viewsets.ViewSet):
    serializer_class = QuestionReportAggregateSerializer
    lookup_field = "question_public_id"

    def get_queryset(self):
        question_public_id = self.kwargs.get(self.lookup_field)
        return QuestionReport.objects.filter(question__public_id=question_public_id)

    def list(self, request, *args, **kwargs):
        # Generate a count of all the report types for this question
        report_data = (
            QuestionReportReason.objects.filter(question_report__in=self.get_queryset())
            .values("reason")
            .annotate(count=Count("reason"))
        )
        return Response(report_data)
