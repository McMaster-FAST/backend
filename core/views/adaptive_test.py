from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..serializers import AdaptiveTestSerializer
from ..models import QuestionGroup

class AdaptiveTestError(Exception):
    pass

class AdaptiveTestView(APIView):
    def get(self, request, *args, **kwargs):
        """
        Handles GET requests for adaptive tests.
        """
        serializer = AdaptiveTestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            question = get_next_question(serializer.validated_data["question_group"])
        except AdaptiveTestError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({"question": question}, status=status.HTTP_200_OK)
    
def get_next_question(question_group_name):
    try:
       question_group = QuestionGroup.objects.get(group_name=question_group_name)
    except QuestionGroup.DoesNotExist:
        raise AdaptiveTestError(f"Question group with name '{question_group_name}' does not exist.")
    return question_group.questions.first().content  # Simplified for demonstration purposes
    