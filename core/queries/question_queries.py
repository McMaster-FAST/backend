import enum
import random

from analytics.models import QuestionAttempt, UserTopicAbilityScore
from core.serializers.adaptive_test.next_question_serializer import (
    NextQuestionSerializer,
)
from ..cat_methods.adaptive_test_model import AdaptiveTestModel
from ..cat_methods.rasch_model import RaschModel
from ..models import (
    AdaptiveTestQuestionMetric,
    Question,
    QuestionOption,
    SavedForLater,
    TestSession,
    TestingParameters,
)
from ..serializers.question_bundle import QuestionBundle
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser

from .resume_queries import update_course_resume_state
from django.db import transaction
from django.db.models import Q
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
    USE_SKIPPED_QUESTIONS = "USE_SKIPPED_QUESTIONS"


class UserSuggestedAction(enum.Enum):
    """
    The action the user should take after finishing a question, based on their current ability and the test parameters.
    """

    STOP_STUDYING = "STOP_STUDYING"


def get_user_unavailable_questions(user: MacFastUser, subtopic: UnitSubtopic):
    
    testing_parameters, _ = TestingParameters.objects.get_or_create(course=subtopic.unit.course)
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)
    excluded = AdaptiveTestQuestionMetric.objects.filter(
        user=user,
        question__subtopic=subtopic,
    ).filter(
        Q(skipped_at_index__gt=test_session.questions_answered_count - testing_parameters.skip_readmit_delay) |
        Q(total_times_seen__gt=testing_parameters.max_question_repetitions)
    ).values_list("question__id", flat=True)
    logger.debug(f"Excluding questions with IDs: {list(excluded)} for user {user.id} in subtopic {subtopic.name}")
    return excluded


@transaction.atomic
def get_next_question_bundle(
    user: MacFastUser, subtopic: UnitSubtopic, model: AdaptiveTestModel = RaschModel
) -> tuple[QuestionBundle | None, list[ContinueActions]]:
    # Keep resume / last-studied subtopic in sync for GET /api/core/resume/
    update_course_resume_state(user, subtopic)

    user_ability, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    current_ability = float(user_ability.score)
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)
    item_difficulty_upper_bound = current_ability + test_session.selection_upper_bound
    item_difficulty_lower_bound = current_ability + test_session.selection_lower_bound

    next_question = select_next_question(
        user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
    )

    if next_question is None:
        return None, determine_continue_actions(user, subtopic), determine_suggested_actions(user, subtopic)

    options = list(QuestionOption.objects.filter(question=next_question))
    random.shuffle(options)
    increment_view_count(user, next_question)
    saved_for_later = SavedForLater.objects.filter(user=user, question=next_question).exists()
    return (
        QuestionBundle(question=next_question, options=options, saved_for_later=saved_for_later),
        [],
        determine_suggested_actions(user, subtopic),
    )


def determine_continue_actions(
    user: MacFastUser, subtopic: UnitSubtopic
) -> list[ContinueActions]:
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)
    user_ability, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    continue_actions = []
    max_visible_difficulty = (
        float(user_ability.score) + test_session.selection_upper_bound
    )
    min_visible_difficulty = (
        float(user_ability.score) + test_session.selection_lower_bound
    )
    if max_visible_difficulty < DIFFICULTY_UPPERBOUND:
        continue_actions.append(ContinueActions.INCREMENT_WINDOW_UPPERBOUND)
    if min_visible_difficulty > DIFFICULTY_LOWERBOUND:
        continue_actions.append(ContinueActions.DECREMENT_WINDOW_LOWERBOUND)

    skip_readmit_delay = TestingParameters.objects.get(
        course=subtopic.unit.course
    ).skip_readmit_delay
    skipped_questions = AdaptiveTestQuestionMetric.objects.filter(
        user=user,
        question__subtopic=subtopic,
        skipped_at_index__gt=test_session.questions_answered_count - skip_readmit_delay,
    )
    if skipped_questions.exists():
        continue_actions.append(ContinueActions.USE_SKIPPED_QUESTIONS)
    return continue_actions


def determine_suggested_actions(
    user: MacFastUser, subtopic: UnitSubtopic
) -> list[UserSuggestedAction]:
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)
    user_ability, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    suggested_actions = []
    stopping_threshold = TestingParameters.objects.get(
        course=subtopic.unit.course
    ).suggested_stopping_threshold
    if (
        float(user_ability.variance) <= stopping_threshold
        and not test_session.has_seen_stop_message
    ):
        suggested_actions.append(UserSuggestedAction.STOP_STUDYING)
        test_session.has_seen_stop_message = True
        test_session.save()
    return suggested_actions


def get_potential_questions(
    user: MacFastUser,
    subtopic: UnitSubtopic,
    item_difficulty_lower_bound: float,
    item_difficulty_upper_bound: float,
):
    all_questions = Question.objects.filter(
        subtopic=subtopic,
        difficulty__gte=item_difficulty_lower_bound,
        difficulty__lte=item_difficulty_upper_bound,
    )
    logger.debug(all_questions)
    potential_questions = all_questions.exclude(
        id__in=get_user_unavailable_questions(user, subtopic)
    )
    return potential_questions


def select_next_question(
    user: MacFastUser,
    subtopic: UnitSubtopic,
    item_difficulty_lower_bound: float,
    item_difficulty_upper_bound: float,
):
    potential_questions = get_potential_questions(
        user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
    )
    if not potential_questions.exists():
        return None
    return random.choice(potential_questions)


def raise_window_ceiling(test_session: TestSession):
    user = test_session.user
    subtopic = test_session.subtopic
    test_parameters, _ = TestingParameters.objects.get_or_create(
        course=subtopic.unit.course
    )
    user_topic_ability_score, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    current_ability = float(user_topic_ability_score.score)
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)
    item_difficulty_upper_bound = current_ability + test_session.selection_upper_bound
    item_difficulty_lower_bound = current_ability + test_session.selection_lower_bound

    # Naive: increment window upper bound until we have a potential question.
    potential_questions = get_potential_questions(
        user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
    )

    while (
        not potential_questions.exists()
        and item_difficulty_upper_bound < DIFFICULTY_UPPERBOUND
    ):
        item_difficulty_upper_bound += test_parameters.window_increment
        potential_questions = get_potential_questions(
            user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
        )
    test_session.selection_upper_bound = item_difficulty_upper_bound - current_ability
    test_session.save()


def lower_window_floor(test_session: TestSession):
    user = test_session.user
    subtopic = test_session.subtopic
    test_parameters, _ = TestingParameters.objects.get_or_create(
        course=subtopic.unit.course
    )
    user_topic_ability_score, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    current_ability = float(user_topic_ability_score.score)

    item_difficulty_upper_bound = current_ability + test_session.selection_upper_bound
    item_difficulty_lower_bound = current_ability + test_session.selection_lower_bound

    # Naive: decrement window lower bound until we have a potential question.
    potential_questions = get_potential_questions(
        user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
    )

    while (
        not potential_questions.exists()
        and item_difficulty_lower_bound > DIFFICULTY_LOWERBOUND
    ):
        item_difficulty_lower_bound -= test_parameters.window_increment
        potential_questions = get_potential_questions(
            user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
        )
    test_session.selection_lower_bound = item_difficulty_lower_bound - current_ability
    test_session.save()


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
    question_info, _ = AdaptiveTestQuestionMetric.objects.get_or_create(
        user=user, question=question
    )
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=question.subtopic)
    if question.subtopic_id is not None:
        update_course_resume_state(user, question.subtopic)
    if selected_option is None:
        max_skips = TestingParameters.objects.get(
            course=question.subtopic.unit.course
        ).max_skips
        if question_info.skips_since_last_answer >= max_skips:
            raise TooManySkipsException()
        question_info.skips_since_last_answer += 1
        question_info.skipped_at_index = test_session.questions_answered_count
    else:
        question_info.skips_since_last_answer = 0
        question_info.total_times_seen += 1
    question_info.save()

    new_ability_score, new_variance = model.compute_ability(user, question.subtopic)
    clamped_ability_score = max(
        -3, min(3, new_ability_score)
    )
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
        updated_ability_score=clamped_ability_score,
        time_spent=time_spent,
    )

    UserTopicAbilityScore.objects.update_or_create(
        user=user,
        unit_sub_topic=question.subtopic,
        defaults={"score": clamped_ability_score, "variance": new_variance},
    )
    return True


def increment_view_count(user, question):
    metrics, _ = AdaptiveTestQuestionMetric.objects.get_or_create(
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
