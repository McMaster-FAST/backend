from core.models import Question
from core.queries.question_queries import add_response, get_next_question_bundle
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
        add_response(request.user, question, None)
        question_bundle = get_next_question_bundle(request.user, question.subtopic)
        return response.Response(
            {
                "question": (
                    NextQuestionSerializer(question_bundle).data
                    if question_bundle
                    else None
                )
            },
            status=status.HTTP_200_OK,
        )
