from analytics.models import QuestionAttempt, UserTopicAbilityScore
from ..cat_methods.adaptive_test_model import AdaptiveTestModel
from ..cat_methods.rasch_model import RaschModel
from ..models import (
    AdaptiveTestQuestionMetrics,
    Question,
    QuestionOption,
    TestingParameters,
)
from ..serializers.question_bundle import QuestionBundle
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser
from django.core.cache import cache
from django.db import transaction


def get_next_question_bundle(
    user: MacFastUser, subtopic: UnitSubtopic, model: AdaptiveTestModel = RaschModel
) -> QuestionBundle | None:

    test_parameters: TestingParameters = cache.get_or_set(
        f"test_parameters_{subtopic.unit.course.public_id}",
        default=TestingParameters.objects.get_or_create(course=subtopic.unit.course)[0],
    )

    # We do not want to show questions that have been recently skipped, or seen too many times.
    unavailable_qs = AdaptiveTestQuestionMetrics.objects.filter(
        user=user,
        questions_since_last_skipped__lt=test_parameters.skip_readmit_delay,
        total_times_seen__gte=test_parameters.max_question_repetitions,
    ).values_list("question_id", flat=True)

    next_question = model.select_next_item(
        user, subtopic, test_parameters, unavailable_qs
    )
    if next_question is None:
        return None

    options = QuestionOption.objects.filter(question=next_question)

    increment_view_count(user, next_question)

    return QuestionBundle(question=next_question, options=options)


@transaction.atomic
def add_response(
    user: MacFastUser,
    question: Question,
    selected_option: QuestionOption,
    time_spent: float = 0.0,
    model: AdaptiveTestModel = RaschModel,
) -> None:
    """
    Records the user's response to a question, updates the ability score, and updates the question metrics.

    @param user:
    @param question:
    @param selected_option: The option selected by the user. If the user skipped the question, this should be None.
    """
    question_info, _ = AdaptiveTestQuestionMetrics.objects.get_or_create(
        user=user, question=question
    )
    if selected_option is None:
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


def increment_view_count(user, question):
    metrics, _ = AdaptiveTestQuestionMetrics.objects.get_or_create(
        user=user, question=question
    )
    metrics.total_times_seen += 1
    metrics.save()
