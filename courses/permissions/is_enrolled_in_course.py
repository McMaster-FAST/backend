from rest_framework.permissions import BasePermission
from ..models import Course, Enrollment


class IsEnrolledInCourse(BasePermission):
    """
    Object-level permission to only allow access to a Course
    if the user has an Enrollment record for it.
    """

    message = "You must be enrolled in this course to view it."

    def has_permission(self, request, view):
        # 1. "Student or higher" means they must be logged in.
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 1. Bypass for Admin/Staff (Optional, but recommended)
        if request.user.is_superuser or request.user.is_staff:
            return True

        # 2. Safety Check: Ensure 'obj' is actually a Course
        # This prevents a crash if you accidentally apply this to a Question ViewSet
        if not isinstance(obj, Course):
            return False

        # 3. Check Enrollment
        # This returns True for both Students AND Instructors
        return Enrollment.objects.filter(user=request.user, course=obj).exists()
