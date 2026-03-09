import enum

from analytics.models import QuestionAttempt, UserTopicAbilityScore
from core.serializers.adaptive_test.next_question_serializer import (
    NextQuestionSerializer,
)
from ..cat_methods.adaptive_test_model import AdaptiveTestModel
from ..cat_methods.rasch_model import RaschModel
from ..models import (
    AdaptiveTestQuestionMetrics,
    Question,
    QuestionOption,
    TestSession,
    TestingParameters,
)
from ..serializers.question_bundle import QuestionBundle
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser
from django.db import transaction
from rest_framework.response import Response
from rest_framework import status
from logging import getLogger

logger = getLogger(__name__)

DIFFICULTY_UPPERBOUND = 3
DIFFICULTY_LOWERBOUND = -3


class ContinueActions(enum.Enum):
    """
    Anything the user should be suggested to do after answering a question
    """

    INCREMENT_WINDOW_UPPERBOUND = "INCREMENT_WINDOW_UPPERBOUND"
    DECREMENT_WINDOW_LOWERBOUND = "DECREMENT_WINDOW_LOWERBOUND"


class UserSuggestedAction(enum.Enum):
    """
    The action the user should take after finishing a question, based on their current ability and the test parameters.
    """

    STOP_STUDYING = "STOP_STUDYING"

@transaction.atomic
def get_next_question_bundle(
    user: MacFastUser, subtopic: UnitSubtopic, model: AdaptiveTestModel = RaschModel
) -> tuple[QuestionBundle | None, list[ContinueActions]]:

    test_parameters, _ = TestingParameters.objects.get_or_create(
        course=subtopic.unit.course
    )
    # We do not want to show questions that have been recently skipped, or seen too many times.
    unavailable_qs = AdaptiveTestQuestionMetrics.objects.filter(
        user=user,
        question__subtopic=subtopic,
        questions_since_last_skipped__lt=test_parameters.skip_readmit_delay,
        total_times_seen__gte=test_parameters.max_question_repetitions,
    ).values_list("question_id", flat=True)

    logger.info(
        f"Unavailable questions for user {user.id} in subtopic {subtopic.id}: {list(unavailable_qs)}"
    )
    next_question = model.select_next_item(user, subtopic, unavailable_qs)
    continue_actions = []
    suggested_actions = []
    if next_question is None:
        test_session, _ = TestSession.objects.get_or_create(
            user=user, subtopic=subtopic
        )
        user_ability, _ = UserTopicAbilityScore.objects.get_or_create(
            user=user, unit_sub_topic=subtopic
        )

        if (
            float(user_ability.score) + test_session.selection_upper_bound
            < DIFFICULTY_UPPERBOUND
        ):
            continue_actions.append(ContinueActions.INCREMENT_WINDOW_UPPERBOUND)
        if (
            float(user_ability.score) - test_session.selection_lower_bound
            > DIFFICULTY_LOWERBOUND
        ):
            continue_actions.append(ContinueActions.DECREMENT_WINDOW_LOWERBOUND)
        if float(user_ability.variance) <= test_parameters.suggested_stopping_threshold and not test_session.has_seen_stop_message:
            suggested_actions.append(UserSuggestedAction.STOP_STUDYING)
            test_session.has_seen_stop_message = True
            test_session.save()
        return None, continue_actions, suggested_actions

    options = QuestionOption.objects.filter(question=next_question)
    increment_view_count(user, next_question)
    return (
        QuestionBundle(question=next_question, options=options),
        [],
        suggested_actions,
    )

class TooManySkipsException(Exception):
    pass

@transaction.atomic
def add_response(
    user: MacFastUser,
    question: Question,
    selected_option: QuestionOption,
    time_spent: float = 0.0,
    model: AdaptiveTestModel = RaschModel,
) -> bool:
    """
    Records the user's response to a question, updates the ability score, and updates the question metrics.

    @param user:
    @param question:
    @param selected_option: The option selected by the user. If the user skipped the question, this should be None.

    @return: True if the response was recorded successfully, False if the action failed
    """
    question_info, _ = AdaptiveTestQuestionMetrics.objects.get_or_create(
        user=user, question=question
    )
    if selected_option is None:
        max_skips = TestingParameters.objects.get(course=question.subtopic.unit.course).max_skips
        if question_info.total_times_skipped >= max_skips:
            raise TooManySkipsException()
        question_info.total_times_skipped += 1
        question_info.questions_since_last_skipped = 0
    else:
        # It might not currently be a "skipped" question but that doesn't matter
        question_info.questions_since_last_skipped += 1
        question_info.total_times_seen += 1
    question_info.save()

    new_ability_score, new_variance = model.compute_ability(user, question.subtopic)

    if selected_option is not None:
        answered_correctly = selected_option.is_answer
        skipped = False
    else:
        skipped = True
        answered_correctly = False

    QuestionAttempt.objects.create(
        question=question,
        user=user,
        answered_correctly=answered_correctly,
        skipped=skipped,
        updated_ability_score=new_ability_score,
        time_spent=time_spent,
    )

    UserTopicAbilityScore.objects.update_or_create(
        user=user,
        unit_sub_topic=question.subtopic,
        defaults={"score": new_ability_score, "variance": new_variance},
    )
    return True


def increment_view_count(user, question):
    metrics, _ = AdaptiveTestQuestionMetrics.objects.get_or_create(
        user=user, question=question
    )
    metrics.total_times_seen += 1
    metrics.save()


def getQuestionResponse(question_bundle, continue_actions, suggested_actions):
    return Response(
        {
            "question": (
                NextQuestionSerializer(question_bundle).data
                if question_bundle
                else None
            ),
            "continue_actions": [action.value for action in continue_actions],
            "suggested_actions": [action.value for action in suggested_actions],
        },
        status=status.HTTP_200_OK,
    )
