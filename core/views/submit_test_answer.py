from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..serializers import AnswerSerializer
from ..models import QuestionOption, Question
from analytics.models import UserTopicAbilityScore

from decimal import Decimal
import math
from scipy.optimize import minimize_scalar


class SubmitTestAnswerView(APIView):
    def post(self, request):
        serializer = AnswerSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        selected_option_id = serializer.validated_data.get("selected_option_id")
        correct_option_id = get_correct_answer_id(
            serializer.validated_data.get("question_id")
        )
        ability_score = UserTopicAbilityScore.objects.get(
            user=request.user,
            unit_sub_topic=Question.objects.get(
                public_id=serializer.validated_data.get("question_id")
            ).subtopic,
        )
        theta, variance = get_updated_theta_variance(
            ability_score.score,
            ability_score.variance,
            Question.objects.get(
                public_id=serializer.validated_data.get("question_id")
            ),
            selected_option_id == correct_option_id,
        )

        ability_score.score = Decimal(theta)
        ability_score.variance = Decimal(variance)
        ability_score.save()

        explanation = Question.objects.get(
            public_id=serializer.validated_data.get("question_id")
        ).answer_explanation
        # TODO: What if the explanation has images?
        response = AnswerSerializer(
            {"correct_option_id": correct_option_id, "explanation": explanation}
        )

        return Response(response.data, status=status.HTTP_200_OK)


def get_correct_answer_id(question_id):
    option = QuestionOption.objects.filter(
        question__public_id=question_id, is_answer=True
    )
    if option.exists():
        return option.first().public_id
    return ""


def p_3pl(theta, a, b, c):
    return c + (1 - c) / (1 + math.exp(-a * (theta - b)))


def dP_3pl(theta, a, b, c):
    P = p_3pl(theta, a, b, c)
    P_star = (P - c) / (1 - c)
    return a * (1 - c) * P_star * (1 - P_star)


def log_posterior(theta, items, responses, theta_prior, var_prior):
    loglike = 0.0
    for (a, b, c), u in zip(items, responses):
        P = p_3pl(theta, a, b, c)
        loglike += u * math.log(P) + (1 - u) * math.log(1 - P)
    logprior = -0.5 * ((theta - theta_prior) ** 2) / var_prior
    return -(loglike + logprior)  # minimize negative


def item_information(theta, a, b, c):
    P = p_3pl(theta, a, b, c)
    dP = dP_3pl(theta, a, b, c)
    return (dP**2) / (P * (1 - P))


# single-item incremental update
def get_updated_theta_variance(
    theta_prior: Decimal, var_prior: Decimal, question, response
):
    item_params = (
        float(question.discrimination),
        float(question.difficulty),
        float(question.guessing),
    )

    items = [item_params]
    responses = [response]
    var_prior = float(var_prior)
    theta_prior = float(theta_prior)
    # MAP update
    res = minimize_scalar(
        log_posterior,
        args=(items, responses, theta_prior, var_prior),
        bounds=(-4, 4),
        method="bounded",
    )
    theta_post = res.x
    a, b, c = item_params
    info = item_information(theta_post, a, b, c)
    var_post = 1.0 / (info + 1.0 / var_prior)
    return theta_post, var_post
