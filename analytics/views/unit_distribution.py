from django.db.models import Count

from analytics.models import QuestionAttempt
from analytics.serializers import UnitDistributionRequestSerializer
from analytics.serializers import UnitDistributionResponseSerializer
from analytics.views.base import BaseAnalyticsView


class UnitDistributionView(BaseAnalyticsView):
    request_serializer_class = UnitDistributionRequestSerializer
    response_serializer_class = UnitDistributionResponseSerializer

    def _get_statistics(self, course_id: int) -> list[dict]:
        statistics = (
            QuestionAttempt.objects.filter(
                question__subtopic__unit__course_id=course_id
            )
            .values(
                'user__id',
                'question__subtopic__unit__id',
                'question__subtopic__unit__name',
                'question__subtopic__unit__number',
            )
            .annotate(
                total_attempts=Count('id'),
                questions_attempted=Count('question', distinct=True),
            )
            .order_by(
                'user__id',
                'question__subtopic__unit__number',
            )
        )

        statistics_list = []
        for stat in statistics:
            statistics_list.append(
                {
                    'user_id': stat['user__id'],
                    'unit_id': stat['question__subtopic__unit__id'],
                    'unit_name': stat['question__subtopic__unit__name'],
                    'unit_number': stat['question__subtopic__unit__number'],
                    'total_attempts': stat['total_attempts'],
                    'questions_attempted': stat['questions_attempted'],
                }
            )

        return statistics_list
