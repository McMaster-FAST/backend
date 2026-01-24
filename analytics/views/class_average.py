from rest_framework.views import APIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from django.db.models import Q
from django.db.models import Avg, Count, FloatField
from django.db.models.functions import Cast
from django.contrib.auth.models import AbstractUser

from analytics.models import QuestionAttempt
from analytics.serializers import (
    ClassAverageRequestSerializer,
    ClassAverageResponseSerializer,
)
from courses.models import Course, Enrolment


class ClassAverageView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        course_id = self._validate_request(request)
        self._check_permission(request.user, course_id)

        statistics = self._get_statistics(course_id)
        response_data = {"course_id": course_id, "statistics": statistics}
        return Response(
            ClassAverageResponseSerializer(response_data).data,
            status=status.HTTP_200_OK,
        )

    def _validate_request(self, request: Request) -> int:
        serializer = ClassAverageRequestSerializer(data=request.query_params)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        course_id = serializer.validated_data["course_id"]

        if not Course.objects.filter(id=course_id).exists():
            raise NotFound("Course not found.")

        return course_id

    def _check_permission(self, user: AbstractUser, course_id: int) -> None:
        if user.is_staff:
            return

        has_access = (
            Enrolment.objects.filter(user=user, course_id=course_id)
            .filter(Q(is_instructor=True) | Q(is_ta=True))
            .exists()
        )

        if not has_access:
            raise PermissionDenied()

    def _get_statistics(self, course_id: int) -> list[dict]:
        statistics = (
            QuestionAttempt.objects.filter(
                question__subtopic__unit__course_id=course_id
            )
            .values(
                "question__subtopic__id",
                "question__subtopic__name",
                "question__subtopic__unit__id",
                "question__subtopic__unit__name",
                "question__subtopic__unit__number",
            )
            .annotate(
                average_score=Avg(
                    Cast("answered_correctly", output_field=FloatField())
                ),
                average_time_spent=Avg("time_spent"),
                total_attempts=Count("id"),
                unique_students=Count("user", distinct=True),
            )
            .order_by(
                "question__subtopic__unit__number",
                "question__subtopic__id",
            )
        )

        statistics_list = []
        for stat in statistics:
            statistics_list.append(
                {
                    "unit_id": stat["question__subtopic__unit__id"],
                    "unit_name": stat["question__subtopic__unit__name"],
                    "unit_number": stat["question__subtopic__unit__number"],
                    "subtopic_id": stat["question__subtopic__id"],
                    "subtopic_name": stat["question__subtopic__name"],
                    "average_score": round(stat["average_score"] or 0, 4),
                    "average_time_spent": round(stat["average_time_spent"] or 0, 2),
                    "total_attempts": stat["total_attempts"],
                    "unique_students": stat["unique_students"],
                }
            )

        return statistics_list
