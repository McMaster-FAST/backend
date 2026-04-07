import abc

from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from courses.models import Course


class BaseAnalyticsView(APIView, abc.ABC):
    """
    Base view for analytics endpoints.
    Subclasses must define:
    - request_serializer_class: Serializer for validating query params.
    - response_serializer_class: Serializer for the response body.
    - _get_statistics(): Returns the statistics data for the response.
    """

    request_serializer_class: type[serializers.Serializer]
    response_serializer_class: type[serializers.Serializer]

    def get(self, request: Request) -> Response:
        course = self._validate_request(request)

        statistics = self._get_statistics(course.id)
        response_data = {
            'course_public_id': str(course.public_id),
            'statistics': statistics,
        }
        return Response(
            self.response_serializer_class(response_data).data,
            status=status.HTTP_200_OK,
        )

    def _validate_request(self, request: Request) -> Course:
        serializer = self.request_serializer_class(data=request.query_params)
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        course_public_id = serializer.validated_data['course_public_id']

        try:
            course = Course.objects.get(public_id=course_public_id)
        except Course.DoesNotExist:
            raise NotFound('Course not found.')

        return course

    @abc.abstractmethod
    def _get_statistics(self, course_id: int) -> list[dict]:
        pass
