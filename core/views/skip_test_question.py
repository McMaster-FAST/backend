from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Question, TestSession


class SkipTestQuestionView(APIView):
    def post(self, request):
        """
        Handles skipping a test question.
        """
        question_id = request.data.get("question_id")
        course_code = request.data.get("course_code")

        question = Question.objects.get(public_id=question_id)
        user = request.user

        test_session = TestSession.objects.get(user=user, course__code=course_code)
        test_session.excluded_questions.add(question)
        test_session.save()

        return Response(
            {"message": f"Question {question_id} has been skipped."}, status=200
        )
