from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Enrolment


class CourseRoleView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_code, *args, **kwargs):
        base_qs = Enrolment.objects.filter(user=request.user, course__code=course_code)

        is_instructor = base_qs.filter(is_instructor=True).exists()
        is_ta = base_qs.filter(is_ta=True).exists()
        is_instructor_or_ta = base_qs.filter(
            Q(is_instructor=True) | Q(is_ta=True)
        ).exists()

        return Response(
            {
                "course_code": course_code,
                "is_instructor": is_instructor,
                "is_ta": is_ta,
                "is_instructor_or_ta": is_instructor_or_ta,
            },
            status=status.HTTP_200_OK,
        )
