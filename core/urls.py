from django.urls import path

# Import the views from your app's views.py
from .views import PingView, UploadView, TestView

urlpatterns = [
    path("ping/", PingView.as_view(), name="ping"),
    path("upload/", UploadView.as_view(), name="upload"),
    path("test/", TestView.as_view(), name="test")
]
