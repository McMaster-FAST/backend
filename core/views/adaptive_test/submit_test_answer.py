from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ...serializers import AnswerSerializer
from ...models import QuestionOption, Question
from ...queries.question_queries import add_response


class SubmitTestAnswerView(APIView):
    def post(self, request):
        serializer = AnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        selected_option_id = serializer.validated_data.get("selected_option_id")
        question = Question.objects.get(
            public_id=serializer.validated_data.get("question_id")
        )
        selected_option = QuestionOption.objects.get(
            public_id=selected_option_id, question=question
        )
        correct_option_id = get_correct_answer_id(question)

        add_response(request.user, question, selected_option)

        explanation = question.answer_explanation
        # TODO: What if the explanation has images?
        response = AnswerSerializer(
            {"correct_option_id": correct_option_id, "explanation": explanation}
        )

        return Response(response.data, status=status.HTTP_200_OK)


def get_correct_answer_id(question: Question) -> str:
    answer_options = QuestionOption.objects.filter(
        question=question, is_answer=True
    ).first()
    if answer_options:
        return answer_options.public_id
    return ""
