from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from django.shortcuts import get_object_or_404
from ...serializers import NextQuestionSerializer
from core.models import TestSession
from courses.models import UnitSubtopic
from ...queries import get_next_question_bundle

import decimal


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

        current_test_session, _ = TestSession.objects.get_or_create(
            user=user,
            subtopic=subtopic,
            defaults={
                "difficulty_range": 1.0,
            },
        )
        if user.active_subtopic != current_test_session.subtopic:
            user.active_subtopic = current_test_session.subtopic
            user.save()

        question_bundle = get_next_question_bundle(subtopic, user, current_test_session)

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
