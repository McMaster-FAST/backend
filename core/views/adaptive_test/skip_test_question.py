from core.models import Question
from core.queries.question_queries import TooManySkipsException, add_response, get_next_question_bundle, getQuestionResponse
from ...serializers import NextQuestionSerializer
from rest_framework import status, response, views
from django.shortcuts import get_object_or_404


class SkipTestQuestionView(views.APIView):
    def post(self, request):
        """
        Handles skipping a test question.
        """
        question_id = request.data.get("question_id")
        if not question_id:
            return response.Response(
                {"error": "question_id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        question = get_object_or_404(Question, public_id=question_id)
        try:
            add_response(request.user, question, None)
        except TooManySkipsException:
            # The button should be disabled on the frontend, but check here too since UI guards are not sufficient.
            return response.Response(
                {"error": "Question has been skipped too many times."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        question_bundle, continue_actions, suggested_actions, gamification = get_next_question_bundle(request.user, question.subtopic)
        return getQuestionResponse(question_bundle, continue_actions, suggested_actions, gamification)
