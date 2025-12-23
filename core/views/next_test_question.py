from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..serializers import NextQuestionSerializer
from ..models import Question, QuestionOption
from analytics.models import UserTopicAbilityScore
from courses.models import UnitSubtopic

import decimal
import numpy as np


class QuestionBundle:
    def __init__(self, question, options):
        self.question = question
        self.options = options


class NextTestQuestionView(APIView):
    def post(self, request):
        """
        Submits an answer for the adaptive test and gets the next question.
        """
        serializer = NextQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        difficulty_range = decimal.Decimal(5)
        user = request.user

        subtopic = UnitSubtopic.objects.get(
            unit__course__code=serializer.validated_data.get("course_code"),
            unit__name=serializer.validated_data.get("unit_name"),
            name=serializer.validated_data.get("subtopic_name"),
        )
        
        user_score, _ = UserTopicAbilityScore.objects.get_or_create(
            user=user, unit_sub_topic=subtopic
        )
        theta = user_score.score
        possible_questions = Question.objects.filter(
            subtopic=subtopic,
            difficulty__gte=theta - difficulty_range,
            difficulty__lte=theta + difficulty_range,
        )
        next_question = max(
            possible_questions,
            key=lambda q: item_information(
                q.discrimination, q.difficulty, q.guessing, theta
            ),
        )
        
        options = QuestionOption.objects.filter(question=next_question)
        return Response(
            {
                "question": NextQuestionSerializer(
                    QuestionBundle(next_question, options)
                ).data
            },
            status=status.HTTP_200_OK,
        )


def item_information(a, b, c, theta):
    p = c + (1 - c) / (1 + np.exp(-a * (theta - b)))
    q = 1 - p
    return (a**2) * ((q / (p * (1 - c))) * ((p - c) ** 2))
