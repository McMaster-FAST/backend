from django.urls import path

from .views import QuestionsView

# Import the views from your app's views.py
from .views import PingView, UploadView, NextTestQuestionView, SubmitTestAnswerView

urlpatterns = [
    path("ping/", PingView.as_view(), name="ping"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("adaptive-test/next-question", NextTestQuestionView.as_view(), name="adaptive_test_next_question"),
    path("adaptive-test/submit", SubmitTestAnswerView.as_view(), name="adaptive_test_submit"),
    path("questions/", QuestionsView.as_view(), name="question_list"),
]
