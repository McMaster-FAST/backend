from django.contrib.auth.models import AbstractUser
from django.db.models import Q
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course
from courses.models import Enrolment


class BaseAnalyticsView(APIView):
    """
    Base view for analytics endpoints.
    Subclasses must define:
    - request_serializer_class: Serializer for validating query params.
    - response_serializer_class: Serializer for the response body.
    - _get_statistics(): Returns the statistics data for the response.
    """

    permission_classes = [IsAuthenticated]

    # Roles allowed to access this endpoint.
    # Valid values: 'instructor', 'ta', 'student'
    allowed_roles: set[str] = {'instructor', 'ta'}

    request_serializer_class: type[serializers.Serializer]
    response_serializer_class: type[serializers.Serializer]

    def get(self, request: Request) -> Response:
        course_id = self._validate_request(request)
        self._check_permission(request.user, course_id)

        statistics = self._get_statistics(course_id)
        response_data = {'course_id': course_id, 'statistics': statistics}
        return Response(
            self.response_serializer_class(response_data).data,
            status=status.HTTP_200_OK,
        )

    def _validate_request(self, request: Request) -> int:
        serializer = self.request_serializer_class(data=request.query_params)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        course_id = serializer.validated_data['course_id']

        if not Course.objects.filter(id=course_id).exists():
            raise NotFound('Course not found.')

        return course_id

    def _check_permission(self, user: AbstractUser, course_id: int) -> None:
        if user.is_staff:
            return

        if not self.allowed_roles:
            raise PermissionDenied()

        # If 'student' is allowed, any enrolled user can access
        if 'student' in self.allowed_roles:
            has_access = Enrolment.objects.filter(
                user=user, course_id=course_id
            ).exists()
        else:
            filters = Q()
            if 'instructor' in self.allowed_roles:
                filters |= Q(is_instructor=True)
            if 'ta' in self.allowed_roles:
                filters |= Q(is_ta=True)

            has_access = (
                Enrolment.objects.filter(user=user, course_id=course_id)
                .filter(filters)
                .exists()
            )

        if not has_access:
            raise PermissionDenied()

    def _get_statistics(self, course_id: int) -> list[dict]:
        raise NotImplementedError
