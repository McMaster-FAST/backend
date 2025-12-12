from django.urls import path, include

from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from .views import (
    CourseViewSet,
    UnitViewSet,
    SubtopicViewSet,
    StudyAidViewSet,
    EnrolmentViewSet,
)

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")

courses_router = NestedDefaultRouter(router, r"courses", lookup="course")
courses_router.register(r"units", UnitViewSet, basename="course-units")
courses_router.register(r"enrolments", EnrolmentViewSet, basename="course-enrolments")

units_router = NestedDefaultRouter(courses_router, r"units", lookup="unit")
units_router.register(r"subtopics", SubtopicViewSet, basename="unit-subtopics")

subtopic_router = NestedDefaultRouter(units_router, r"subtopics", lookup="subtopic")
subtopic_router.register(r"studyaids", StudyAidViewSet, basename="subtopic-studyaids")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(courses_router.urls)),
    path("", include(units_router.urls)),
    path("", include(subtopic_router.urls)),
]
