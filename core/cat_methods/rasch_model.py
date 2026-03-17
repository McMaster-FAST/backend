from analytics.models import UserTopicAbilityScore
from .adaptive_test_model import AdaptiveTestModel
from .adaptive_test_utils import max_apost, mle
from ..models import (
    TestingParameters,
)
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser
from analytics.models import QuestionAttempt
from logging import getLogger

logger = getLogger(__name__)
class RaschModel(AdaptiveTestModel):
    """
    See https://www.rasch.org/rmt/rmt64cat.htm

    We are using MLE for ability estimation, but only after a certain number of questions have been answered.
    Before that point we use MAP. This helps supposedly...
    """
    
    @staticmethod
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
        logger.debug("User responses for ability estimation: %s", list(responses))
        params = TestingParameters.objects.get_or_create(course=subtopic.unit.course)[0]
        if len(responses) < params.warmpup_length:
            return max_apost(responses, prev_abiltiy_score, prev_variance)
        return mle(responses, prev_abiltiy_score)
