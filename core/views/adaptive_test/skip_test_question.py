from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from core.models import Question

from ...queries import get_next_question_bundle, get_testsession_and_set_active

from ...serializers import NextQuestionSerializer


class SkipTestQuestionView(APIView):
    def post(self, request):
        """
        Handles skipping a test question.
        """
        question_id = request.data.get("question_id")

        question = Question.objects.get(public_id=question_id)
        user = request.user

        test_session = get_testsession_and_set_active(user, question.subtopic)
        test_session.skipped_questions.add(question)

        question_bundle = get_next_question_bundle(
            test_session.subtopic, user, test_session
        )
        test_session.current_question = question_bundle.question if question_bundle else None
        test_session.save()
        return Response(
            {
                "question": (
                    NextQuestionSerializer(question_bundle).data
                    if question_bundle
                    else None
                )
            },
            status=status.HTTP_200_OK,
        )

        