from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from courses.models import Enrolment
from ..models import Question, QuestionOption


class QuestionAnswerView(APIView):
    def get(self, request, public_id):
        is_privileged = Enrolment.objects.filter(
            Q(is_instructor=True) | Q(is_ta=True), user=request.user
        ).exists()
        if not is_privileged:
            return Response(status=status.HTTP_403_FORBIDDEN)

        question = get_object_or_404(Question, public_id=public_id)
        correct_option = get_object_or_404(QuestionOption, question=question, is_answer=True)
        return Response({"correct_option_id": correct_option.public_id}, status=status.HTTP_200_OK)
