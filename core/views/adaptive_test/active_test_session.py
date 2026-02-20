from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound

from ...models import TestSession
from ...serializers import ActiveTestSessionSerializer


class ActiveTestSessionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing the active test session.

    This viewset automatically filters to only show and operate on the test session
    that corresponds to the user's active_subtopic. All CRUD operations are performed
    only on this active session.

    The active test session is determined by:
    - The authenticated user
    - The user's active_subtopic field
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ActiveTestSessionSerializer

    def get_queryset(self):
        """
        Filter to only return the active test session based on the user's active_subtopic.
        Returns an empty queryset if the user has no active_subtopic set.
        """
        user = self.request.user

        if not user.active_subtopic:
            return TestSession.objects.none()

        return TestSession.objects.filter(user=user, subtopic=user.active_subtopic)

    def get_object(self):
        """
        Retrieve the active test session.
        Creates one if it doesn't exist.
        """
        user = self.request.user

        if not user.active_subtopic:
            raise NotFound(detail="No active subtopic set for this user.")

        # Get or create the active test session
        test_session, created = TestSession.objects.get_or_create(
            user=user, subtopic=user.active_subtopic
        )

        return test_session

    def list(self, request, *args, **kwargs):
        """
        Return the active test session as a single object (not a list).
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)

        try:
            instance = self.get_object()
        except NotFound as e:
            return Response({"detail": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)
