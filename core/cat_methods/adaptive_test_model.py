from core.models import AdaptiveTestQuestionMetrics, Question, TestingParameters
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


class AdaptiveTestModel:
    def select_next_item(
        user: MacFastUser,
        subtopic: UnitSubtopic,
        test_parameters: TestingParameters,
        unavailable_qs,
    ) -> Question | None:
        raise NotImplementedError

    def compute_ability(user: MacFastUser) -> float:
        raise NotImplementedError
