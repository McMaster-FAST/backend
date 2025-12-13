from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from ..models import Course, Unit
from ..serializers import UnitSerializer, UnitDetailSerializer
from django.shortcuts import get_object_or_404


class UnitViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]  # Add IsInstructor logic if needed
    serializer_class = UnitSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["course"]

    def get_queryset(self):
        queryset = Unit.objects.select_related("course").order_by("number")

        course_code = self.kwargs.get("course_code")
        if course_code:
            course = get_object_or_404(Course, code=course_code)
            return queryset.filter(course=course)

        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return UnitDetailSerializer

        return super().get_serializer_class()

    def perform_create(self, serializer):
        course_code = self.kwargs.get("course_code")

        if course_code:
            course = Course.objects.get(code=course_code)
            serializer.save(course=course)
        else:
            serializer.save()
