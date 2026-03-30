from analytics.serializers import QuestionReportAggregateSerializer
from django.db.models import Count
from core.models import Question
from courses.models import Course
from rest_framework import viewsets, filters
from MacFAST.pagination import OnlyPageNumberPagination


class QuestionReportAggregateViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionReportAggregateSerializer

    pagination_class = OnlyPageNumberPagination
    page_size = 10

    filter_backends = [filters.SearchFilter]

    search_fields = [
        "content",
    ]

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        course = Course.objects.filter(code=course_code).first()
        return (
            Question.objects.filter(subtopic__unit__course=course)
            .annotate(total_reports=Count("reports"))
            .filter(total_reports__gt=0)
            .order_by("-total_reports", "public_id")
        )
