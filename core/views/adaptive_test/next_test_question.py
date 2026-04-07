from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404
from ...serializers import NextQuestionSerializer
from courses.models import UnitSubtopic
from ...queries.question_queries import get_next_question_bundle, getQuestionResponse


class NextTestQuestionView(APIView):
    def post(self, request):
        """
        Submits an answer for the adaptive test and gets the next question.
        """

        serializer = NextQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        course_code = serializer.validated_data["course_code"]
        unit_name = serializer.validated_data["unit_name"]
        subtopic_name = serializer.validated_data["subtopic_name"]

        # We must find the requested subtopic
        subtopic = get_object_or_404(
            UnitSubtopic,
            unit__course__code=course_code,
            unit__course__is_archived=False,
            unit__name=unit_name,
            name=subtopic_name,
        )
        question_bundle, continue_actions, suggested_actions, gamification = get_next_question_bundle(user, subtopic)
        return getQuestionResponse(question_bundle, continue_actions, suggested_actions, gamification)
