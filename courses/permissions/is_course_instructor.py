from rest_framework.permissions import BasePermission
from django.shortcuts import get_object_or_404
from ..models import UnitSubTopic, Enrollment


class IsCourseInstructor(BasePermission):
    message = "You must be an instructor of this course to perform this action."

    def has_permission(self, request, view):
        """
        Checks access for creating (POST) a Question.
        We must look up the UnitSubTopic ID provided in the request data
        to find the Course, then check Enrollment.
        """
        if request.method == "POST":
            # Assuming your API expects 'unit_sub_topic' ID in the POST body
            subtopic_id = request.data.get("unit_sub_topic")

            if not subtopic_id:
                return False

            # 1. Get the subtopic and traverse to Course
            subtopic = get_object_or_404(UnitSubTopic, pk=subtopic_id)
            course = subtopic.unit.course

            # 2. Check Enrollment table
            return Enrollment.objects.filter(
                user=request.user, course=course, is_instructor=True
            ).exists()

        # Allow safe methods (GET, HEAD, OPTIONS) or handle list filtering in ViewSet
        return True

    def has_object_permission(self, request, view, obj):
        """
        Checks access for Editing/Deleting (PUT, PATCH, DELETE).
        'obj' is the Question instance (assuming Question links to UnitSubTopic).
        """
        # 1. Traverse up: Question -> UnitSubTopic -> Unit -> Course
        # Note: Adjust 'unit_sub_topic' below if your field name is different on the Question model
        course = obj.unit_sub_topic.unit.course

        # 2. Check Enrollment table
        return Enrollment.objects.filter(
            user=request.user, course=course, is_instructor=True
        ).exists()
