from core.queries.question_queries import lower_window_floor, raise_window_ceiling, repeat_questions, restart_session
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
        test_session = self.get_object()
        raise_window_ceiling(test_session)
        test_session.refresh_from_db()
        response_serializer = self.get_serializer(test_session)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        

    @action(
        detail=True,
        methods=["post"],
        url_path="update-sel-window/lower-bound",
        url_name="update-selection-lower-bound",
    )
    def update_selection_lower_bound(self, request, *args, **kwargs):
        test_session = self.get_object()
        lower_window_floor(test_session)
        test_session.refresh_from_db()
        response_serializer = self.get_serializer(test_session)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path="repeat-questions",
        url_name="repeat-questions",
    )
    def repeat_questions_action(self, request, *args, **kwargs):
        test_session = self.get_object()
        repeat_questions(test_session)
        test_session.refresh_from_db()
        return Response(self.get_serializer(test_session).data, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["post"],
        url_path="restart-session",
        url_name="restart-session",
    )
    def restart_session_action(self, request, *args, **kwargs):
        test_session = self.get_object()
        restart_session(test_session)
        test_session.refresh_from_db()
        return Response(self.get_serializer(test_session).data, status=status.HTTP_200_OK)

    def _get_test_parameters(self, test_session: TestSession):
        return TestingParameters.objects.get(course=test_session.subtopic.unit.course)
