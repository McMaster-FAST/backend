from core.models import Question
from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


class AdaptiveTestModel:

    @staticmethod
    def compute_ability(user: MacFastUser, subtopic: UnitSubtopic) -> float:
        raise NotImplementedError
