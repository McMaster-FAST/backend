from django.contrib import admin
from .models import Course, Unit, UnitSubTopic, UserScoreForTopic, Enrollment


class UnitSubTopicInline(admin.TabularInline):
    """
    Allows adding/editing UnitSubTopics directly inside the Unit admin page.
    """

    model = UnitSubTopic
    extra = 1  # Show one blank slot for a new sub-topic
    autocomplete_fields = ["question_group"]


class UnitInline(admin.StackedInline):
    """
    Allows adding/editing Units directly inside the Course admin page.
    We use StackedInline here because each Unit will also show
    its own 'UnitSubTopicInline' beneath it, giving a full tree view.
    """

    model = Unit
    extra = 1  # Show one blank slot for a new unit
    show_change_link = True


class EnrollmentInline(admin.TabularInline):
    """
    Allows adding/editing Enrollments (students/instructors)
    directly inside the Course admin page.
    """

    model = Enrollment
    extra = 1
    autocomplete_fields = ["user"]


# --- MODEL ADMINS ---


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "year", "semester")
    search_fields = ("name", "code")
    list_filter = ("year", "semester")

    # From one Course page, you can manage all its Units and Enrollments.
    inlines = [UnitInline, EnrollmentInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "number", "course")
    search_fields = ("name", "course__name")
    list_filter = ("course__name",)
    autocomplete_fields = ["course"]

    inlines = [UnitSubTopicInline]


@admin.register(UnitSubTopic)
class UnitSubTopicAdmin(admin.ModelAdmin):
    list_display = ("name", "unit", "question_group")
    search_fields = ("name", "unit__name")
    autocomplete_fields = ["unit", "question_group"]


@admin.register(UserScoreForTopic)
class UserScoreForTopicAdmin(admin.ModelAdmin):
    list_display = ("user", "unit_sub_topic", "score")
    search_fields = (
        "user__username",
        "unit_sub_topic__name",
    )  # Assumes user has 'username'
    list_filter = ("score",)
    autocomplete_fields = ["user", "unit_sub_topic"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "is_instructor")
    search_fields = ("user__username", "course__name")
    list_filter = ("is_instructor", "course__name")
    autocomplete_fields = ["user", "course"]
