"""
Resume / last-studied subtopic per (user, course).

Used by GET /api/core/resume/ and must stay in sync when users use adaptive test.
"""

from courses.models import UnitSubtopic
from sso_auth.models import MacFastUser

from ..models import CourseResumeState


def update_course_resume_state(user: MacFastUser, subtopic: UnitSubtopic) -> None:
    """
    Upsert the last studied subtopic for this user and the subtopic's course.

    Safe to call frequently (single update_or_create); idempotent for same subtopic.
    """
    if subtopic is None:
        return
    course = subtopic.unit.course
    CourseResumeState.objects.update_or_create(
        user=user,
        course=course,
        defaults={"last_subtopic": subtopic},
    )
