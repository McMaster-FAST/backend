from django.urls import path, include

from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from .views import (
    CourseViewSet,
    UnitViewSet,
    SubtopicViewSet,
    StudyAidViewSet,
    EnrolmentViewSet,
)

from core.views import QuestionViewSet, OptionViewSet

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"units", UnitViewSet, basename="units")
router.register(r"subtopics", SubtopicViewSet, basename="subtopics")
router.register(r"questions", QuestionViewSet, basename="questions")

courses_router = NestedDefaultRouter(router, r"courses", lookup="course")
courses_router.register(r"units", UnitViewSet, basename="course-units")
courses_router.register(r"enrolments", EnrolmentViewSet, basename="course-enrolments")

units_router = NestedDefaultRouter(router, r"units", lookup="unit")
units_router.register(r"subtopics", SubtopicViewSet, basename="unit-subtopics")

subtopics_router = NestedDefaultRouter(router, r"subtopics", lookup="subtopic")
subtopics_router.register(
    r"study-aids", StudyAidViewSet, basename="subtopic-study-aids"
)
subtopics_router.register(r"questions", QuestionViewSet, basename="subtopic-questions")

questions_router = NestedDefaultRouter(router, r"questions", lookup="question")
questions_router.register(r"options", OptionViewSet, basename="question-options")

urlpatterns = [
    path(r"", include(router.urls)),
    path(r"", include(courses_router.urls)),
    path(r"", include(units_router.urls)),
    path(r"", include(subtopics_router.urls)),
    path(r"", include(questions_router.urls)),
]
