from django.contrib import admin
from .models import QuestionAttempt, UserTopicAbilityScore

# Register your models here.


@admin.register(QuestionAttempt)
class QuestionAnalyticsAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "answered_correctly", "time_spent", "timestamp")
    list_filter = ("answered_correctly", "timestamp")


@admin.register(UserTopicAbilityScore)
class UserTopicAbilityScoreAdmin(admin.ModelAdmin):
    list_display = ("user", "unit_sub_topic", "score")
    search_fields = (
        "user__username",
        "unit_sub_topic__name",
    )
    list_filter = ("score",)
    autocomplete_fields = ["user", "unit_sub_topic"]
