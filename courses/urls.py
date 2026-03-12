from django.urls import path, include

from core.views.adaptive_test.question_metrics_viewset import (
    AdaptiveTestQuestionMetricViewSet,
)
from rest_framework_nested.routers import DefaultRouter, NestedDefaultRouter

from core.views.question_comment_viewset import QuestionCommentViewSet

from .views import (
    CourseViewSet,
    UnitViewSet,
    SubtopicViewSet,
    StudyAidViewSet,
    EnrolmentViewSet,
)

from core.views import OptionViewSet, QuestionViewSet, TestSessionViewSet

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")
router.register(r"units", UnitViewSet, basename="units")
router.register(r"subtopics", SubtopicViewSet, basename="subtopics")
router.register(r"questions", QuestionViewSet, basename="questions")
router.register(r"test-sessions", TestSessionViewSet, basename="test-sessions")
router.register(r"comments", QuestionCommentViewSet, basename="comments")
router.register(r"study-aids", StudyAidViewSet, basename="study-aids")
router.register(r"enrolments", EnrolmentViewSet, basename="enrolments")
router.register(r"adaptive-test/question-metrics", AdaptiveTestQuestionMetricViewSet, basename="adaptive-question-metrics")

courses_router = NestedDefaultRouter(router, r"courses", lookup="course")
courses_router.register(r"units", UnitViewSet, basename="course-units")
courses_router.register(r"enrolments", EnrolmentViewSet, basename="course-enrolments")
courses_router.register(r"questions", QuestionViewSet, basename="course-questions")

units_router = NestedDefaultRouter(router, r"units", lookup="unit")
units_router.register(r"subtopics", SubtopicViewSet, basename="unit-subtopics")

subtopics_router = NestedDefaultRouter(router, r"subtopics", lookup="subtopic")
subtopics_router.register(
    r"study-aids", StudyAidViewSet, basename="subtopic-study-aids"
)
subtopics_router.register(r"questions", QuestionViewSet, basename="subtopic-questions")

questions_router = NestedDefaultRouter(router, r"questions", lookup="question")
questions_router.register(r"options", OptionViewSet, basename="question-options")
questions_router.register(
    r"comments", QuestionCommentViewSet, basename="question-comments"
)

urlpatterns = [
    path(r"", include(router.urls)),
    path(r"", include(courses_router.urls)),
    path(r"", include(units_router.urls)),
    path(r"", include(subtopics_router.urls)),
    path(r"", include(questions_router.urls)),
]
