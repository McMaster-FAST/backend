from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from courses.models import Course, Enrolment

from ..models import CourseResumeState
from ..serializers import ResumeTargetSerializer


def _resolve_course_for_resume(request, course_code: str):
    """
    Find the Course row for this resume request.

    Primary path: Enrolment for (user, course code). That matches how students access courses.

    Fallbacks (why get_object_or_404(Enrolment, ...) was failing):
    - Staff users often see all courses in list views but have *no* Enrolment rows; they may still
      have CourseResumeState after testing adaptive flow.
    - If no Enrolment but resume state exists, use the course FK from that row.
    - If staff and still no row, allow the first Course with this code (same code can exist per
      year/semester via unique_together on Course).
    """
    user = request.user

    enrolment = (
        Enrolment.objects.filter(user=user, course__code=course_code)
        .select_related("course")
        .order_by("-course__year", "-course__semester")
        .first()
    )
    if enrolment:
        return enrolment.course

    resume_for_course = (
        CourseResumeState.objects.filter(user=user, course__code=course_code)
        .select_related("course")
        .order_by("-updated_at")
        .first()
    )
    if resume_for_course:
        return resume_for_course.course

    if user.is_staff:
        return (
            Course.objects.filter(code=course_code)
            .order_by("-year", "-semester")
            .first()
        )

    return None


class ResumeView(APIView):
    
    # Returns the last studied subtopic for a given course and user.
    

    permission_classes = [IsAuthenticated]

    def get(self, request):
        course_code = (request.query_params.get("course_code") or "").strip()
        if not course_code:
            return Response(
                {"detail": "course_code query parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        course = _resolve_course_for_resume(request, course_code)
        if not course:
            return Response(
                {
                    "detail": (
                        "No enrolment or resume data found for this course. "
                        "You must be enrolled in the course (or have progress saved) to resume."
                    )
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            resume_state = CourseResumeState.objects.select_related(
                "course", "last_subtopic", "last_subtopic__unit"
            ).get(user=request.user, course=course)
        except CourseResumeState.DoesNotExist:
            return Response(
                {"detail": "No resume state found for this course."},
                status=status.HTTP_404_NOT_FOUND,
            )

        data = {
            "course_code": resume_state.course.code,
            "unit_name": resume_state.last_subtopic.unit.name,
            "subtopic_name": resume_state.last_subtopic.name,
        }
        serializer = ResumeTargetSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

