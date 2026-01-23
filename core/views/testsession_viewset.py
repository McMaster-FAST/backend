from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from core.models import TestSession
from core.serializers.testsession_serializer import (
    TestSessionSerializer,
    TestSessionWriteSerializer,
)


class TestSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TestSession model.
    - GET: Returns all public fields with nested data
    - POST/PUT/PATCH: Only allows excluded_questions and use_out_of_range_questions
    - Accessible by course code: /api/test-session/<course_code>
    """

    permission_classes = [IsAuthenticated]
    queryset = TestSession.objects.all()
    filter_backends = [DjangoFilterBackend]
    lookup_field = "course__code"

    def get_serializer_class(self):
        """Return different serializers for read and write operations"""
        if self.request.method in ["POST", "PUT", "PATCH"]:
            return TestSessionWriteSerializer
        return TestSessionSerializer

    def get_queryset(self):
        """Filter test sessions to only show user's own sessions"""
        user = self.request.user
        return TestSession.objects.filter(user=user)

    def perform_create(self, serializer):
        """Set the user to the current authenticated user"""
        # Note: course and subtopic should be provided in the request
        serializer.save(user=self.request.user)
