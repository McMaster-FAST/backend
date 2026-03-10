from django.urls import path

from .views.class_average import ClassAverageView
from .views.time_per_question import TimePerQuestionView
from .views.unit_distribution import UnitDistributionView

urlpatterns = [
    path("class-averages/", ClassAverageView.as_view(), name="class_averages"),
    path("time-per-question/", TimePerQuestionView.as_view(), name="time_per_question"),
    path("unit-distribution/", UnitDistributionView.as_view(), name="unit_distribution"),
    path("time-per-question/", TimePerQuestionView.as_view(), name="time_per_question"),
    path("unit-distribution/", UnitDistributionView.as_view(), name="unit_distribution"),
]
