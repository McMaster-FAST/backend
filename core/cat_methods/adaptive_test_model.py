from core.models import Question
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


class AdaptiveTestModel:
    def select_next_item(
        user: MacFastUser,
        subtopic: UnitSubtopic,
        unavailable_qs,
    ) -> Question | None:
        raise NotImplementedError

    def compute_ability(user: MacFastUser) -> float:
        raise NotImplementedError
