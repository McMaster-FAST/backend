from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ...serializers import NextQuestionSerializer

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

        # TODO: Adjust difficulty range as needed
        difficulty_range = decimal.Decimal(5)
        user = request.user

        question_bundle = get_next_question_bundle(
            serializer.validated_data.get("course_code"),
            serializer.validated_data.get("unit_name"),
            serializer.validated_data.get("subtopic_name"),
            user,
            difficulty_range,
        )
        if question_bundle is None:
            return Response(
                {"message": "No more questions available in this subtopic."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(
            {"question": NextQuestionSerializer(question_bundle).data},
            status=status.HTTP_200_OK,
        )
