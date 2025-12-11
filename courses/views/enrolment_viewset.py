from rest_framework import viewsets
from django.db.models import Q
from ..models import Enrolment
from ..serializers import EnrolmentSerializer
from ..permissions import IsEnrolmentManager


class EnrolmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrolmentSerializer
    permission_classes = [IsEnrolmentManager]

    def get_queryset(self):
        user = self.request.user

        # Admins see all enrolments
        if user.is_staff:
            return Enrolment.objects.all()

        # Instructors & TAs see enrolments ONLY for courses they manage.
        # Logic:
        # a. Find all courses where I am Instructor OR TA
        # b. Return all enrolments that belong to those courses

        my_managed_courses = (
            Enrolment.objects.filter(user=user)
            .filter(Q(is_instructor=True) | Q(is_ta=True))
            .values_list("course", flat=True)
        )

        return Enrolment.objects.filter(course__in=my_managed_courses)
