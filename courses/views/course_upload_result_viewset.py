from courses.models import QuestionUploadResult
from courses.serializers.course_upload_result_serializer import (
    CourseUploadResultSerializer,
)
from rest_framework import permissions, viewsets
from django_filters.rest_framework import DjangoFilterBackend


class CourseTaskResultViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CourseUploadResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "public_id"

    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "result": ["exact"],
    }

    def get_queryset(self):
        course_code = self.kwargs.get("course_code")
        public_id = self.kwargs.get("public_id")
        user = self.request.user

        queryset = QuestionUploadResult.objects.filter(course__code=course_code, initiating_user=user)
        if public_id:
            queryset = queryset.filter(public_id=public_id)
        return queryset
