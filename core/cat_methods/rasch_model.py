from analytics.models import UserTopicAbilityScore
from core.cat_methods.adaptive_test_model import AdaptiveTestModel
from core.cat_methods.adaptive_test_utils import max_apost, mle
from core.models import (
    Question,
    TestingParameters,
)
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser
from analytics.models import QuestionAttempt
import random
from django.core.cache import cache

class RaschModel(AdaptiveTestModel):
    """
    See https://www.rasch.org/rmt/rmt64cat.htm

    We are using MLE for ability estimation, but only after a certain number of questions have been answered.
    This is supposed to help...
    """

    def select_next_item(
        user: MacFastUser,
        subtopic: UnitSubtopic,
        test_parameters: TestingParameters,
        unavailable_qs: list[int],
    ) -> Question:
        user_topic_ability_score, _ = UserTopicAbilityScore.objects.get_or_create(
            user=user, unit_sub_topic=subtopic
        )
        current_ability = float(user_topic_ability_score.score)

        item_difficulty_lower_bound = (
            current_ability - test_parameters.question_selection_window
        )
        item_difficulty_upper_bound = (
            current_ability + test_parameters.question_selection_window
        )
        potential_questions = Question.objects.filter(
            subtopic=subtopic,
            difficulty__gte=item_difficulty_lower_bound,
            difficulty__lte=item_difficulty_upper_bound,
        ).exclude(id__in=unavailable_qs)

        if not potential_questions.exists():
            return None

        return random.choice(potential_questions)

    def compute_ability(
        user: MacFastUser, subtopic: UnitSubtopic
    ) -> tuple[float, float]:
        user_topic_ability_score, _ = UserTopicAbilityScore.objects.get_or_create(
            user=user, unit_sub_topic=subtopic
        )
        prev_abiltiy_score = float(user_topic_ability_score.score)
        prev_variance = float(user_topic_ability_score.variance)

        responses = QuestionAttempt.objects.filter(
            user=user, question__subtopic=subtopic, skipped=False
        ).values_list("question__difficulty", "answered_correctly")

        params: TestingParameters = cache.get(TestingParameters.get_cache_name(subtopic.unit.course.public_id), default=TestingParameters.objects.get_or_create(course=subtopic.unit.course)[0])
        if len(responses) < params.warmpup_length:
            return max_apost(responses, prev_abiltiy_score, prev_variance)
        return mle(responses, prev_abiltiy_score)
