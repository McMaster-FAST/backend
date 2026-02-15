from django.db.models import Avg
from django.db.models import Count
from django.db.models import FloatField
from django.db.models.functions import Cast

from analytics.models import QuestionAttempt
from analytics.serializers import ClassAverageRequestSerializer
from analytics.serializers import ClassAverageResponseSerializer
from analytics.views.base import BaseAnalyticsView


class ClassAverageView(BaseAnalyticsView):
    request_serializer_class = ClassAverageRequestSerializer
    response_serializer_class = ClassAverageResponseSerializer

    def _get_statistics(self, course_id: int) -> list[dict]:
        statistics = (
            QuestionAttempt.objects.filter(
                question__subtopic__unit__course_id=course_id
            )
            .values(
                'question__subtopic__id',
                'question__subtopic__name',
                'question__subtopic__unit__id',
                'question__subtopic__unit__name',
                'question__subtopic__unit__number',
            )
            .annotate(
                average_score=Avg(
                    Cast('answered_correctly', output_field=FloatField())
                ),
                total_attempts=Count('id'),
                unique_students=Count('user', distinct=True),
            )
            .order_by(
                'question__subtopic__unit__number',
                'question__subtopic__id',
            )
        )

        statistics_list = []
        for stat in statistics:
            statistics_list.append(
                {
                    'unit_id': stat['question__subtopic__unit__id'],
                    'unit_name': stat['question__subtopic__unit__name'],
                    'unit_number': stat['question__subtopic__unit__number'],
                    'subtopic_id': stat['question__subtopic__id'],
                    'subtopic_name': stat['question__subtopic__name'],
                    'average_score': round(stat['average_score'] or 0, 4),
                    'total_attempts': stat['total_attempts'],
                    'unique_students': stat['unique_students'],
                }
            )

        return statistics_list
