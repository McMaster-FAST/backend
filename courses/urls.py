from django.urls import path, include

from rest_framework.routers import DefaultRouter

from .views import (
    CourseViewSet,
    UnitViewSet,
    SubtopicViewSet,
    StudyAidViewSet,
    EnrolmentViewSet,
)

router = DefaultRouter()
router.register(r"units", UnitViewSet, basename="units")
router.register(r"subtopics", SubtopicViewSet, basename="subtopics")
router.register(r"studyaids", StudyAidViewSet, basename="studyaids")
router.register(r"enrolments", EnrolmentViewSet, basename="enrolments")

router.register(r"", CourseViewSet, basename="courses")

urlpatterns = [
    path("", include(router.urls)),
]
