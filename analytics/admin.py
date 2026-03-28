from django.contrib import admin
from .models import (
    QuestionAttempt,
    QuestionReport,
    QuestionReportReason,
    UserTopicAbilityScore,
    CourseXP,
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


@admin.register(CourseXP)
class CourseXPAdmin(admin.ModelAdmin):
    verbose_name_plural = "Course XP"

    list_display = ("user", "course", "total_xp", "display_level", "display_progress")

    list_filter = ("course",)
    search_fields = ("user__email", "user__username", "course__name", "course__code")

    readonly_fields = ("display_level", "display_xp_info", "display_progress")

    @admin.display(description="Current Level")
    def display_level(self, obj):
        return obj.level

    @admin.display(description="Progress (%)")
    def display_progress(self, obj):
        return f"{obj.progress_percentage}%"

    @admin.display(description="XP Breakdown")
    def display_xp_info(self, obj):
        return f"{obj.xp_in_current_level} / {obj.xp_for_next_level} XP (Current Level)"

    # Organize the detail page layout
    fieldsets = (
        (None, {"fields": ("user", "course", "total_xp")}),
        (
            "Calculated Progress",
            {
                "fields": ("display_level", "display_xp_info", "display_progress"),
                "description": "These values are calculated based on the exponential doubling formula.",
            },
        ),
    )
