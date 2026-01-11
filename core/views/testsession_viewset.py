from ..serializers import TestSessionSerializer
from ..models import TestSession
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated


class TestSessionViewSet(viewsets.ModelViewSet):
    serializer_class = TestSessionSerializer
    lookup_field = "course__code"
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # if user.is_staff:
        #     return TestSession.objects.all()

        return TestSession.objects.filter(
            user=user,
            course__code=self.kwargs.get("course__code", None),
        )
