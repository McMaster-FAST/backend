from django.urls import path

from .views import ClassAverageView
from .views import TimePerQuestionView
from .views import UnitDistributionView

urlpatterns = [
    path("class-averages/", ClassAverageView.as_view(), name="class_averages"),
    path("time-per-question/", TimePerQuestionView.as_view(), name="time_per_question"),
    path("unit-distribution/", UnitDistributionView.as_view(), name="unit_distribution"),
]
