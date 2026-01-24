from django.urls import path

from .views import ClassAverageView

urlpatterns = [
    path("class-averages/", ClassAverageView.as_view(), name="class_averages"),
]
