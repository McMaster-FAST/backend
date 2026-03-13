from django.contrib import admin
from .models import (
    QuestionAttempt,
    QuestionReport,
    QuestionReportReason,
    UserTopicAbilityScore,
)

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


class QuestionReportReasonInline(admin.TabularInline):
    model = QuestionReportReason
    extra = 1


@admin.register(QuestionReport)
class QuestionReportAdmin(admin.ModelAdmin):
    list_display = ("question", "user", "timestamp")
    inlines = [QuestionReportReasonInline]


@admin.register(QuestionReportReason)
class QuestionReportReasonAdmin(admin.ModelAdmin):
    list_display = ("question_report", "reason")
