from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from ..models import Question
from ..serializers import QuestionSerializer

class QuestionsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        """
        Retrieves all questions.
        """
        questions = Question.objects.all()
        questions_data = QuestionSerializer(questions, many=True).data
        return Response({"questions": questions_data}, status=status.HTTP_200_OK)

