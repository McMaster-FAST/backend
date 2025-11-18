from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from ..serializers import AnswerSerializer
from ..models import QuestionOption

class SubmitTestAnswerView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = AnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data

        selected_answer = data["selected_answer"]

        # TODO: This is definitely the wrong way to do this but for now we are just going to 
        # take in an option id and return whether it is marked as an answer or not.

        if is_answer_correct(selected_answer):
            response_data = {"correct": True}
        else:
            response_data = {"correct": False}
        return Response(response_data, status=status.HTTP_200_OK)
    
def is_answer_correct(answer):
    return QuestionOption.objects.filter(id=answer, is_answer=True).exists()
    