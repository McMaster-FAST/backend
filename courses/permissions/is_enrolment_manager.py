from rest_framework import permissions
from ..models import Enrolment


class IsEnrolmentManager(permissions.BasePermission):
    # See github wiki for detailed explanation of logic:

    def has_permission(self, request, view):
        # Block unauthenticated users immediately
        if not request.user.is_authenticated:
            return False

        # Allow Admins
        if request.user.is_staff:
            return True

        # For Create, defer the check to the Serializer
        # because we need to know which course they are trying to enrol a student
        if request.method == "POST":
            return True

        # we allow because 'get_queryset' will filter out anything they don't have access to
        return True

    def has_object_permission(self, request, view, obj):
        # Admins can do anything
        if request.user.is_staff:
            return True

        # Check the user's role in the course this enrolment belongs to
        try:
            requester_enrolment = Enrolment.objects.get(
                user=request.user, course=obj.course
            )
        except Enrolment.DoesNotExist:
            return False  # They aren't even in the course

        # Only Instructors (and Admins)
        if request.method == "DELETE":
            return requester_enrolment.is_instructor

        # Instructors OR TAs
        if request.method in ["PUT", "PATCH"]:
            return requester_enrolment.is_instructor or requester_enrolment.is_ta

        # Instructors OR TAs
        return requester_enrolment.is_instructor or requester_enrolment.is_ta
