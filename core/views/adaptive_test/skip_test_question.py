from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import Question, TestSession

from ...queries import get_next_question_bundle

from ...serializers import NextQuestionSerializer


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

        subtopic = TestSession.objects.get(user=user, course__code=course_code).subtopic
        unit = subtopic.unit
        course = unit.course
        next_question_bundle = get_next_question_bundle(
            course.code, unit.name, subtopic.name, user, difficulty_range=5
        )

        if next_question_bundle is None:
            return Response(
                {"message": "No more questions available in this subtopic."},
                status=404,
            )
        return Response(
            {"next_question": NextQuestionSerializer(next_question_bundle).data},
            status=200,
        )
