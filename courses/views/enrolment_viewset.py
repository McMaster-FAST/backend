from rest_framework import viewsets
from django.db.models import Q
from courses.models import Enrolment, Course
from courses.serializers import EnrolmentSerializer
from rest_framework.permissions import IsAuthenticated


class EnrolmentViewSet(viewsets.ModelViewSet):
    serializer_class = EnrolmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_staff:
            queryset = Enrolment.objects.all()
        else:
            my_managed_courses = (
                Enrolment.objects.filter(user=user)
                .filter(Q(is_instructor=True) | Q(is_ta=True))
                .values_list("course", flat=True)
            )

            queryset = Enrolment.objects.filter(course__in=my_managed_courses)

        course_code = self.kwargs.get("course_code")

        if course_code:
            queryset = queryset.filter(course__code=course_code)

        return queryset

    def perform_create(self, serializer):
        course_code = self.kwargs.get("course_code")
        if course_code:
            course = Course.objects.get(code=course_code)
            serializer.save(course=course)
        else:
            serializer.save()
