from django.urls import path

from .views.saved_for_later_viewset import SavedForLaterViewSet

# Import the views from your app's views.py
from .views import (
    PingView,
    UploadView,
    NextTestQuestionView,
    SubmitTestAnswerView,
    SkipTestQuestionView,
    QuestionsView,
    ActiveTestSessionViewSet,
)

ADAPTIVE_TEST_BASE_PATH = "adaptive-test/"
urlpatterns = [
    path("ping/", PingView.as_view(), name="ping"),
    path("upload/", UploadView.as_view(), name="upload"),
    path(
        f"{ADAPTIVE_TEST_BASE_PATH}next-question/",
        NextTestQuestionView.as_view(),
        name="next-test-question",
    ),
    path(
        f"{ADAPTIVE_TEST_BASE_PATH}submit-answer/",
        SubmitTestAnswerView.as_view(),
        name="submit-test-answer",
    ),
    path(
        f"{ADAPTIVE_TEST_BASE_PATH}skip-question/",
        SkipTestQuestionView.as_view(),
        name="skip-test-question",
    ),
    path(
        "test-sessions/active/",
        ActiveTestSessionViewSet.as_view(
            {
                "get": "list",
                "put": "update",
                "patch": "partial_update",
            }
        ),
        name="active-test-session",
    ),
    path("questions/", QuestionsView.as_view(), name="questions"),
    path(
        "saved-for-later/<str:course_code>/",
        SavedForLaterViewSet.as_view(
            {"get": "list", "post": "create", "delete": "destroy"}
        ),
        name="saved-for-later",
    ),
]
