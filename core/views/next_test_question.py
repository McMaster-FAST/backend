from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status

from ..serializers import NextQuestionSerializer, AdaptiveTestQuestionSerializer, AdaptiveTestQuestionBundle
from ..models import QuestionGroup, QuestionOption

class AdaptiveTestError(Exception):
    pass

class NextTestQuestionView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        """
        Submits an answer for the adaptive test and gets the next question.
        """
        serializer = NextQuestionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Here you would process the submitted answer and update the adaptive test state
            # For simplicity, we will just get the next question
            question, options = get_next_question_data(serializer.validated_data["group_name"])
            response_serializer = AdaptiveTestQuestionSerializer(AdaptiveTestQuestionBundle(question, options))
            return Response({"question": response_serializer.data}, status=status.HTTP_200_OK)
        except AdaptiveTestError as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
def get_next_question_data(question_group_name):
    try:
       group_name = QuestionGroup.objects.get(group_name=question_group_name)
    except QuestionGroup.DoesNotExist:
        raise AdaptiveTestError(f"Question group with name '{question_group_name}' does not exist.")
    
    # TODO: Select question based on adaptive algorithm
    # The issue is that the existing python library for adaptive testing loads ALL the questions into 
    # a dataframe and uses that to track the test. We probably can't to that here. Can we repurpose 
    # question group to temporarily store quesitons that haven't been asked yet.
    selected_question = group_name.questions.order_by('?').first() 
    options = QuestionOption.objects.filter(question=selected_question)
    return selected_question, options
    