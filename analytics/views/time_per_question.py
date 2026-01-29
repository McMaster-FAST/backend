from django.db.models import Avg
from django.db.models import Count

from analytics.models import QuestionAttempt
from analytics.serializers import TimePerQuestionRequestSerializer
from analytics.serializers import TimePerQuestionResponseSerializer
from analytics.views.base import BaseAnalyticsView


class TimePerQuestionView(BaseAnalyticsView):
    request_serializer_class = TimePerQuestionRequestSerializer
    response_serializer_class = TimePerQuestionResponseSerializer

    def _get_statistics(self, course_id: int) -> list[dict]:
        statistics = (
            QuestionAttempt.objects.filter(
                question__subtopic__unit__course_id=course_id
            )
            .values(
                'question__id',
                'question__serial_number',
                'question__subtopic__id',
                'question__subtopic__name',
                'question__subtopic__unit__id',
                'question__subtopic__unit__name',
                'question__subtopic__unit__number',
            )
            .annotate(
                average_time_spent=Avg('time_spent'),
                total_attempts=Count('id'),
                unique_students=Count('user', distinct=True),
            )
            .order_by(
                'question__subtopic__unit__number',
                'question__subtopic__id',
                'question__id',
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
                    'question_id': stat['question__id'],
                    'question_serial_number': stat['question__serial_number'],
                    'average_time_spent': round(stat['average_time_spent'] or 0, 2),
                    'total_attempts': stat['total_attempts'],
                    'unique_students': stat['unique_students'],
                }
            )

        return statistics_list
