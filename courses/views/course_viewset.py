from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from courses.models import Course
from courses.serializers import CourseSerializer, CourseDetailSerializer


class CourseViewSet(viewsets.ModelViewSet):
    serializer_class = CourseSerializer
    lookup_field = "code"
    # The user must be logged in AND satisfy the instructor check for edits
    # permission_classes = [IsAuthenticated, IsInstructorOrReadOnly]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # If user is staff, return all courses
        if user.is_staff:
            return Course.objects.all()

        # User can only see courses they are enrolled in
        return Course.objects.filter(enrolment__user=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer
