from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.response import Response

from core.models import TestSession, TestingParameters
from core.serializers import TestSessionSerializer

SELECTION_UPPER_BOUND_NAME = "selection_upper_bound"
SELECTION_LOWER_BOUND_NAME = "selection_lower_bound"

class TestSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TestSessionSerializer
    lookup_field = "subtopic__public_id"
    lookup_url_kwarg = "subtopic_public_id"
    http_method_names = ["get", "put", "patch", "post", "options"]

    def get_queryset(self):
        return TestSession.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed("POST")

    @action(
        detail=True,
        methods=["post"],
        url_path="update-sel-window/upper-bound",
        url_name="update-selection-upper-bound",
    )
    def update_selection_upper_bound(self, request, *args, **kwargs):
        return self._update_selection_bound(request, SELECTION_UPPER_BOUND_NAME)

    @action(
        detail=True,
        methods=["post"],
        url_path="update-sel-window/lower-bound",
        url_name="update-selection-lower-bound",
    )
    def update_selection_lower_bound(self, request, *args, **kwargs):
        return self._update_selection_bound(request, SELECTION_LOWER_BOUND_NAME)

    def _update_selection_bound(self, request, field_name: str):
        test_session = self.get_object()
        test_parameters = TestingParameters.objects.get(course=test_session.subtopic.unit.course)
        if (field_name == SELECTION_UPPER_BOUND_NAME):
            setattr(test_session, field_name, getattr(test_session, field_name) + test_parameters.window_increment)
        elif (field_name == SELECTION_LOWER_BOUND_NAME):
            setattr(test_session, field_name, getattr(test_session, field_name) - test_parameters.window_increment)
        test_session.save(update_fields=[field_name])

        response_serializer = self.get_serializer(test_session)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
