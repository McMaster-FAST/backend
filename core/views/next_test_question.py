from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..serializers import NextQuestionSerializer, AdaptiveTestQuestionSerializer, QuestionBundle
from ..models import Question, QuestionOption, TestSession
from analytics.models import UserTopicAbilityScore
from sso_auth.models import MacFastUser
from courses.models import UnitSubtopic

import decimal
import numpy as np

class AdaptiveTestError(Exception):
    pass

class NextTestQuestionView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Submits an answer for the adaptive test and gets the next question.
        """
        serializer = NextQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        difficulty_range = decimal.Decimal(0.5)
        user = MacFastUser.objects.get(username="PWardell86")  # Placeholder for actual user authentication

        subtopic = UnitSubtopic.objects.get(
            unit__course__code=serializer.validated_data.get("course_code"),
            unit__name=serializer.validated_data.get("unit_name"), 
            name=serializer.validated_data.get("subtopic_name")
        )

        test_session, created = TestSession.objects.get_or_create(
            user=user,
            subtopic=subtopic,
        )
        if created:
            # Initialize test session with questions from the subtopic
            questions = Question.objects.filter(subtopic=test_session.subtopic)
            test_session.questions.set(questions)
            test_session.save()
            return Response({"question": None, "message": "Test session created. Please request the next question."}, status=status.HTTP_200_OK)


        user_score, _ = UserTopicAbilityScore.objects.get_or_create(
            user=user, 
            unit_sub_topic=subtopic
        )

        theta = user_score.score

        possible_questions = test_session.questions.filter(
            difficulty__gte=theta - difficulty_range, 
            difficulty__lte=theta + difficulty_range
        )

        next_question = max(possible_questions, key=lambda q: item_information(q.discrimination, q.difficulty, q.guessing, theta), default=None)
        if not next_question:
            return Response({"question": None, "message": "No suitable next question found."}, status=status.HTTP_200_OK)
        try:
            options = QuestionOption.objects.filter(question=next_question)
            return Response({"question": AdaptiveTestQuestionSerializer(QuestionBundle(next_question, options)).data}, status=status.HTTP_200_OK)
        except AdaptiveTestError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def item_information(a, b, c, theta):
    p = c + (1 - c) / (1 + np.exp(-a * (theta - b)))
    q = 1 - p
    return (a**2) * ((q / (p * (1-c))) * ((p - c)**2))
    