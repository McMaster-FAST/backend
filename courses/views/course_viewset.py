from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from analytics.models import UserTopicAbilityScore
from courses.models import Course, UnitSubtopic
from courses.serializers import CourseSerializer, CourseDetailSerializer

from django.db.models import Prefetch


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
            queryset = Course.objects.all()
        else:
            queryset = None

        if self.action == "retrieve":
            # Filter scores, only prefetch the ones for the current user
            user_scores_qs = UserTopicAbilityScore.objects.filter(user=user)

            # Build prefetch chain: Course -> Unit -> Subtopic -> Score
            return queryset.prefetch_related(
                Prefetch(
                    "unit_set__unitsubtopic_set",
                    queryset=UnitSubtopic.objects.prefetch_related(
                        Prefetch(
                            "usertopicabilityscore_set",
                            queryset=user_scores_qs,
                            to_attr="prefetched_scores",
                        )
                    ),
                )
            )

        # User can only see courses they are enrolled in
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer
