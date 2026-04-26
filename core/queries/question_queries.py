import enum
import random

from analytics.models import CourseXP, QuestionAttempt, UserTopicAbilityScore
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
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from rest_framework.response import Response
from rest_framework import status
from logging import getLogger

logger = getLogger(__name__)

DIFFICULTY_UPPERBOUND = 3
DIFFICULTY_LOWERBOUND = -3
COURSE_DIFFICULTY_SAMPLE_SIZE = 200
COURSE_DIFFICULTY_THRESHOLDS_TTL_SECONDS = 60 * 30


class ContinueActions(enum.Enum):
    """
    Anything the user should be suggested to do after answering a question
    """

    INCREMENT_WINDOW_UPPERBOUND = "INCREMENT_WINDOW_UPPERBOUND"
    DECREMENT_WINDOW_LOWERBOUND = "DECREMENT_WINDOW_LOWERBOUND"
    USE_SKIPPED_QUESTIONS = "USE_SKIPPED_QUESTIONS"
    # All questions are on cooldown but can come back — offer a reduced-spacing repeat
    REPEAT_QUESTIONS = "REPEAT_QUESTIONS"
    # All questions have been permanently exhausted (seen max_repetitions times)
    RESTART_SESSION = "RESTART_SESSION"


class UserSuggestedAction(enum.Enum):
    """
    The action the user should take after finishing a question, based on their current ability and the test parameters.
    """

    STOP_STUDYING = "STOP_STUDYING"


def get_user_unavailable_questions(user: MacFastUser, subtopic: UnitSubtopic):

    testing_parameters, _ = TestingParameters.objects.get_or_create(
        course=subtopic.unit.course
    )
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)
    excluded = (
        AdaptiveTestQuestionMetric.objects.filter(
            user=user,
            question__subtopic=subtopic,
        )
        .filter(
            Q(
                skipped_at_index__gt=test_session.questions_answered_count
                - testing_parameters.skip_readmit_delay
            )
            | Q(total_times_seen__gt=testing_parameters.max_question_repetitions)
            | Q(
                last_seen_at_index__gt=test_session.questions_answered_count
                - testing_parameters.min_questions_between_repitions
            )
        )
        .values_list("question__id", flat=True)
    )
    logger.debug(
        f"Excluding questions with IDs: {list(excluded)} for user {user.id} in subtopic {subtopic.name}"
    )
    return excluded


def _recovery_actions(user: MacFastUser, subtopic: UnitSubtopic) -> list[ContinueActions]:
    """Returns REPEAT_QUESTIONS or RESTART_SESSION depending on question exhaustion state.
    Single-question subtopics always get RESTART_SESSION — repeating one question
    with a gap is meaningless."""
    testing_parameters, _ = TestingParameters.objects.get_or_create(
        course=subtopic.unit.course
    )
    all_questions = Question.objects.filter(subtopic=subtopic)
    if not all_questions.exists():
        return []
    if all_questions.count() == 1:
        return [ContinueActions.RESTART_SESSION]
    permanently_exhausted_ids = AdaptiveTestQuestionMetric.objects.filter(
        user=user,
        question__subtopic=subtopic,
        total_times_seen__gt=testing_parameters.max_question_repetitions,
    ).values_list("question__id", flat=True)
    if not all_questions.exclude(id__in=permanently_exhausted_ids).exists():
        return [ContinueActions.RESTART_SESSION]
    return [ContinueActions.REPEAT_QUESTIONS]


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

    # Single-question subtopics: skip all window/repeat logic. Either show the
    # question (if available) or tell the user to restart — nothing else applies.
    is_single_question_subtopic = Question.objects.filter(subtopic=subtopic).count() == 1
    if is_single_question_subtopic:
        next_question = select_next_question(
            user, subtopic, DIFFICULTY_LOWERBOUND, DIFFICULTY_UPPERBOUND
        )
        suggested_actions = determine_suggested_actions(user, subtopic)
        if next_question is None:
            return (
                None,
                [ContinueActions.RESTART_SESSION],
                suggested_actions,
                build_gamification_data(user, subtopic, None),
            )
        options = list(QuestionOption.objects.filter(question=next_question))
        random.shuffle(options)
        increment_view_count(user, next_question)
        saved_for_later = SavedForLater.objects.filter(user=user, question=next_question).exists()
        return (
            QuestionBundle(question=next_question, options=options, saved_for_later=saved_for_later),
            [ContinueActions.RESTART_SESSION] if UserSuggestedAction.STOP_STUDYING in suggested_actions else [],
            suggested_actions,
            build_gamification_data(user, subtopic, next_question),
        )

    item_difficulty_upper_bound = current_ability + test_session.selection_upper_bound
    item_difficulty_lower_bound = current_ability + test_session.selection_lower_bound

    next_question = select_next_question(
        user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
    )

    if next_question is None:
        # For a session that hasn't started yet, auto-expand the window so the user
        # always gets a first question instead of an immediate dead-end prompt.
        if test_session.questions_answered_count == 0:
            raise_window_ceiling(test_session)
            lower_window_floor(test_session)
            test_session.refresh_from_db()
            item_difficulty_upper_bound = current_ability + test_session.selection_upper_bound
            item_difficulty_lower_bound = current_ability + test_session.selection_lower_bound
            next_question = select_next_question(
                user, subtopic, item_difficulty_lower_bound, item_difficulty_upper_bound
            )

    suggested_actions = determine_suggested_actions(user, subtopic)

    if next_question is None:
        continue_actions = determine_continue_actions(user, subtopic)
    else:
        continue_actions = []

    # When the algorithm suggests stopping, also surface recovery options so the
    # user isn't left with only "Return to course page".
    if UserSuggestedAction.STOP_STUDYING in suggested_actions:
        for action in _recovery_actions(user, subtopic):
            if action not in continue_actions:
                continue_actions.append(action)

    if next_question is None:
        return (
            None,
            continue_actions,
            suggested_actions,
            build_gamification_data(user, subtopic, None),
        )

    options = list(QuestionOption.objects.filter(question=next_question))
    random.shuffle(options)
    increment_view_count(user, next_question)
    saved_for_later = SavedForLater.objects.filter(user=user, question=next_question).exists()
    return (
        QuestionBundle(question=next_question, options=options, saved_for_later=saved_for_later),
        continue_actions,
        suggested_actions,
        build_gamification_data(user, subtopic, next_question),
    )


def determine_continue_actions(
    user: MacFastUser, subtopic: UnitSubtopic
) -> list[ContinueActions]:
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)
    user_ability, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    testing_parameters = TestingParameters.objects.get(course=subtopic.unit.course)

    all_questions = Question.objects.filter(subtopic=subtopic)

    # Single-question subtopics skip window/repeat logic entirely — only restart makes sense.
    if all_questions.count() == 1:
        return [ContinueActions.RESTART_SESSION]

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

    skipped_questions = AdaptiveTestQuestionMetric.objects.filter(
        user=user,
        question__subtopic=subtopic,
        skipped_at_index__gt=test_session.questions_answered_count - testing_parameters.skip_readmit_delay,
    )
    if skipped_questions.exists():
        continue_actions.append(ContinueActions.USE_SKIPPED_QUESTIONS)

    # Detect exhausted / all-on-cooldown states so the frontend can offer recovery
    if all_questions.exists():
        permanently_exhausted_ids = AdaptiveTestQuestionMetric.objects.filter(
            user=user,
            question__subtopic=subtopic,
            total_times_seen__gt=testing_parameters.max_question_repetitions,
        ).values_list("question__id", flat=True)

        not_permanently_exhausted = all_questions.exclude(id__in=permanently_exhausted_ids)

        if not not_permanently_exhausted.exists():
            continue_actions.append(ContinueActions.RESTART_SESSION)
        else:
            on_cooldown_ids = AdaptiveTestQuestionMetric.objects.filter(
                user=user,
                question__subtopic=subtopic,
                last_seen_at_index__gt=test_session.questions_answered_count
                - testing_parameters.min_questions_between_repitions,
            ).values_list("question__id", flat=True)

            truly_available = not_permanently_exhausted.exclude(id__in=on_cooldown_ids)
            if not truly_available.exists():
                continue_actions.append(ContinueActions.REPEAT_QUESTIONS)

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
    test_session.refresh_from_db()
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
    test_session, _ = TestSession.objects.get_or_create(
        user=user, subtopic=question.subtopic
    )
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
        test_session.questions_answered_count += 1
        test_session.save()
    question_info.save()

    new_ability_score, new_variance = model.compute_ability(user, question.subtopic)
    clamped_ability_score = max(-3, min(3, new_ability_score))
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

    if answered_correctly:
        course = question.subtopic.unit.course
        xp_record, _ = CourseXP.objects.get_or_create(
            user=user, course=course, defaults={"total_xp": 0}
        )

        # Your new balanced economy
        base_xp = 10
        scaling_factor = 2
        min_xp = 5
        max_xp = 15

        difficulty_delta = float(question.difficulty) - clamped_ability_score

        # Calculate raw XP
        raw_xp = round(base_xp + (scaling_factor * difficulty_delta))

        # Clamp the XP so it never drops below 5 or goes above 15
        xp_earned = max(min_xp, min(max_xp, raw_xp))

        xp_record.total_xp += xp_earned
        xp_record.save()

    return True


def increment_view_count(user, question):
    test_session, _ = TestSession.objects.get_or_create(
        user=user, subtopic=question.subtopic
    )
    metrics, _ = AdaptiveTestQuestionMetric.objects.get_or_create(
        user=user, question=question
    )
    metrics.total_times_seen += 1
    metrics.last_seen_at_index = test_session.questions_answered_count
    metrics.save()

# Helper function to calculate the percentile of a list of values
def _percentile(sorted_values: list[float], percentile_rank: float) -> float:
    if not sorted_values:
        return 0.0

    if len(sorted_values) == 1:
        return sorted_values[0]

    index = (len(sorted_values) - 1) * percentile_rank
    lower = int(index)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = index - lower
    return (1 - weight) * sorted_values[lower] + weight * sorted_values[upper]


def _get_default_difficulty_label(difficulty: float) -> str:
    if difficulty > 1.8:
        return "MUCH_HARDER"
    elif difficulty > 0.6:
        return "HARDER"
    elif difficulty >= -0.6:
        return "ON_TARGET"
    elif difficulty >= -1.8:
        return "EASIER"
    return "MUCH_EASIER"

# Helper function to get the difficulty thresholds for a course
def _get_course_difficulty_thresholds(course_id: str) -> tuple[float, float, float, float] | None:
    cache_key = f"course_difficulty_thresholds_{course_id}"
    cached_thresholds = cache.get(cache_key)
    if cached_thresholds is not None:
        return cached_thresholds

    course_questions = Question.objects.filter(
        subtopic__unit__course_id=course_id,
        is_active=True,
    )
    total_questions = course_questions.count()
    if total_questions < 5:
        return None

    if total_questions > COURSE_DIFFICULTY_SAMPLE_SIZE:
        sampled_difficulties = list(
            course_questions.order_by("?").values_list("difficulty", flat=True)[
                :COURSE_DIFFICULTY_SAMPLE_SIZE
            ]
        )
    else:
        sampled_difficulties = list(course_questions.values_list("difficulty", flat=True))

    if len(sampled_difficulties) < 5:
        return None

    sorted_difficulties = sorted(float(value) for value in sampled_difficulties)
    thresholds = (
        _percentile(sorted_difficulties, 0.2),
        _percentile(sorted_difficulties, 0.4),
        _percentile(sorted_difficulties, 0.6),
        _percentile(sorted_difficulties, 0.8),
    )
    cache.set(cache_key, thresholds, timeout=COURSE_DIFFICULTY_THRESHOLDS_TTL_SECONDS)
    return thresholds


def _get_difficulty_label(difficulty: float, subtopic: UnitSubtopic) -> str:
    thresholds = _get_course_difficulty_thresholds(str(subtopic.unit.course_id))
    if thresholds is None:
        return _get_default_difficulty_label(difficulty)

    p20, p40, p60, p80 = thresholds
    print(f"Thresholds: {p20}, {p40}, {p60}, {p80}")

    if difficulty >= p80:
        return "MUCH_HARDER"
    elif difficulty >= p60:
        return "HARDER"
    elif difficulty >= p40:
        return "ON_TARGET"
    elif difficulty >= p20:
        return "EASIER"
    return "MUCH_EASIER"


def build_gamification_data(
    user: MacFastUser, subtopic: UnitSubtopic, question: Question | None
) -> dict:
    user_ability, _ = UserTopicAbilityScore.objects.get_or_create(
        user=user, unit_sub_topic=subtopic
    )
    test_session, _ = TestSession.objects.get_or_create(user=user, subtopic=subtopic)

    ability_score = float(user_ability.score)
    ability_variance = float(user_ability.variance)

    recent_correct = (
        QuestionAttempt.objects.filter(
            user=user,
            question__subtopic=subtopic,
            skipped=False,
        )
        .order_by("-timestamp")
        .values_list("answered_correctly", flat=True)[:20] # only check the last 20 questions
    )
    streak = 0
    for correct in recent_correct:
        if correct:
            streak += 1
        else:
            break

    gamification: dict = {
        "user_ability": round(ability_score, 4),
        "ability_variance": round(ability_variance, 4),
        "questions_answered": test_session.questions_answered_count,
        "current_streak": streak,
    }

    if question is not None:
        question_difficulty = float(question.difficulty)
        difficulty_delta = round(question_difficulty - ability_score, 4)
        gamification.update(
            {
                "question_difficulty": question_difficulty,
                "difficulty_delta": difficulty_delta,
                "difficulty_label": _get_difficulty_label(
                    question_difficulty, subtopic
                ),
            }
        )

    return gamification


def repeat_questions(test_session: TestSession):
    """
    All questions are on cooldown. Move non-exhausted questions out of cooldown so at
    least one next-question call can succeed immediately after the user presses repeat.
    """
    testing_parameters, _ = TestingParameters.objects.get_or_create(
        course=test_session.subtopic.unit.course
    )
    permanently_exhausted_ids = AdaptiveTestQuestionMetric.objects.filter(
        user=test_session.user,
        question__subtopic=test_session.subtopic,
        total_times_seen__gt=testing_parameters.max_question_repetitions,
    ).values_list("question__id", flat=True)

    eligible_count = Question.objects.filter(
        subtopic=test_session.subtopic
    ).exclude(id__in=permanently_exhausted_ids).count()

    eligible_metrics = AdaptiveTestQuestionMetric.objects.filter(
        user=test_session.user,
        question__subtopic=test_session.subtopic,
    ).exclude(total_times_seen__gt=testing_parameters.max_question_repetitions)

    if eligible_count > 1:
        # Make repeated questions eligible immediately for the current answer index.
        # This avoids a no-question loop where repeat requires answering one more
        # question before any candidate unlocks.
        new_index = (
            test_session.questions_answered_count
            - testing_parameters.min_questions_between_repitions
        )
        eligible_metrics.update(last_seen_at_index=new_index)
    else:
        # Only 1 question available — make it immediately accessible.
        eligible_metrics.update(last_seen_at_index=None)


def restart_session(test_session: TestSession):
    """
    All questions have been permanently exhausted. Reset question metrics so the
    user can go through the subtopic again from scratch.
    """
    AdaptiveTestQuestionMetric.objects.filter(
        user=test_session.user,
        question__subtopic=test_session.subtopic,
    ).update(
        total_times_seen=0,
        last_seen_at_index=None,
        skipped_at_index=None,
        skips_since_last_answer=0,
    )
    test_session.questions_answered_count = 0
    test_session.selection_upper_bound = 0.5
    test_session.selection_lower_bound = -0.5
    test_session.has_seen_stop_message = False
    test_session.save()


def getQuestionResponse(question_bundle, continue_actions, suggested_actions, gamification=None):
    return Response(
        {
            "question": (
                NextQuestionSerializer(question_bundle).data
                if question_bundle
                else None
            ),
            "continue_actions": [action.value for action in continue_actions],
            "suggested_actions": [action.value for action in suggested_actions],
            "gamification": gamification or {},
        },
        status=status.HTTP_200_OK,
    )
