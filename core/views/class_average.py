from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

# We added Case and When to the imports
from django.db.models import Avg, Count, Case, When, FloatField

# Import your specific models
from courses.models import Course, Unit
from ..models import QuestionAnalytics

from ..serializers import CourseAnalyticsSerializer


class CourseUnitPerformanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)

        # 1. Get all Units
        units = (
            Unit.objects.filter(course=course)
            .values("id", "name", "number")
            .order_by("number")
        )

        # 2. Define the path to the unit
        unit_lookup = "question__questiongroup__unitsubtopic__unit__id"

        # 3. Calculate USER Stats (Using Case/When instead of Cast)
        user_stats = (
            QuestionAnalytics.objects.filter(
                user=request.user,
                question__questiongroup__unitsubtopic__unit__course=course,
            )
            .values(unit_lookup)
            .annotate(
                # FIX IS HERE: Convert True->1.0, False->0.0 manually
                accuracy=Avg(
                    Case(
                        When(answered_correctly=True, then=1.0),
                        default=0.0,
                        output_field=FloatField(),
                    )
                ),
                attempts=Count("id"),
            )
        )

        user_map = {item[unit_lookup]: item for item in user_stats}

        # 4. Calculate CLASS Stats (Using Case/When instead of Cast)
        class_stats = (
            QuestionAnalytics.objects.filter(
                question__questiongroup__unitsubtopic__unit__course=course
            )
            .values(unit_lookup)
            .annotate(
                # FIX IS HERE
                accuracy=Avg(
                    Case(
                        When(answered_correctly=True, then=1.0),
                        default=0.0,
                        output_field=FloatField(),
                    )
                )
            )
        )

        class_map = {item[unit_lookup]: item for item in class_stats}

        # 5. Merge Data (Logic remains the same)
        results = []
        for unit in units:
            u_id = unit["id"]

            u_data = user_map.get(u_id, {})
            u_acc = u_data.get("accuracy") or 0.0
            u_count = u_data.get("attempts") or 0

            c_data = class_map.get(u_id, {})
            c_acc = c_data.get("accuracy") or 0.0

            results.append(
                {
                    "unit_id": u_id,
                    "unit_number": unit["number"],
                    "unit_name": unit["name"],
                    "user_accuracy": round(u_acc * 100, 1),
                    "class_accuracy": round(c_acc * 100, 1),
                    "questions_attempted": u_count,
                }
            )

        data = {
            "course_code": course.code,
            "course_name": course.name,
            "units": results,
        }

        serializer = CourseAnalyticsSerializer(data)
        return Response(serializer.data)
