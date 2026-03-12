from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser


def set_user_active_subtopic(user: MacFastUser, subtopic: UnitSubtopic) -> None:
    # Premature/ unnecessary optimization?
    if user.active_subtopic != subtopic:
        user.active_subtopic = subtopic
        user.save()
