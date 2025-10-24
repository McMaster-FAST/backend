from django.urls import path

# Import the views from your app's views.py
from .views import PingView

urlpatterns = [
    path("ping/", PingView.as_view(), name="ping"),
]
