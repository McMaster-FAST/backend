from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from ..models import Course, Unit
from ..serializers import UnitSerializer, UnitDetailSerializer


class UnitViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # Add IsInstructor logic if needed

    def get_queryset(self):
        return Unit.objects.filter(course__code=self.kwargs["course_code"])

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UnitDetailSerializer  # Returns Unit -> Subtopics
        return UnitSerializer

    def perform_create(self, serializer):
        course = Course.objects.get(code=self.kwargs["course_code"])
        serializer.save(course=course)
