# analytics/views.py

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from courses.models import Course
from analytics.models import CourseXP
from analytics.serializers import CourseXPSerializer


class CourseXPViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet to retrieve a user's XP for a specific course.
    Read-only to prevent frontend tampering with XP values.
    """

    serializer_class = CourseXPSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filters the queryset to only include the logged-in user's XP
        for the course specified in the nested URL.
        """
        course_code = self.kwargs.get("course_code")

        if course_code:
            # 1. Fetch the actual Course object using your established pattern
            course = get_object_or_404(Course, code=course_code)
            # 2. Filter using the object
            return CourseXP.objects.filter(user=self.request.user, course=course)

        return CourseXP.objects.none()  # Fallback if no course_code is provided

    def list(self, request, *args, **kwargs):
        """
        Overrides the default list behavior.
        Instead of returning an array with one item, it returns the single XP object.
        If the user has no XP record yet, it returns a default starting payload.
        """
        xp_record = self.get_queryset().first()

        if not xp_record:
            course_code = self.kwargs.get("course_code")
            return Response(
                {
                    "course": course_code,
                    "total_xp": 0,
                    "level": 1,
                    "xp_in_current_level": 0,
                    "xp_for_next_level": 100,
                    "progress_percentage": 0,
                }
            )

        serializer = self.get_serializer(xp_record)
        return Response(serializer.data)
