from django.contrib import admin
from .models import Course, Unit, UnitSubtopic, Enrolment, StudyAid, AidType
from core.models import Question


class UnitSubtopicInline(admin.TabularInline):
    """
    Allows adding/editing UnitSubtopics directly inside the Unit admin page.
    """

    model = UnitSubtopic
    extra = 1  # Show one blank slot for a new sub-topic


class UnitInline(admin.StackedInline):
    """
    Allows adding/editing Units directly inside the Course admin page.
    We use StackedInline here because each Unit will also show
    its own 'UnitSubtopicInline' beneath it, giving a full tree view.
    """

    model = Unit
    extra = 1  # Show one blank slot for a new unit
    show_change_link = True


class EnrolmentInline(admin.TabularInline):
    """
    Allows adding/editing Enrolments (students/instructors)
    directly inside the Course admin page.
    """

    model = Enrolment
    extra = 1
    autocomplete_fields = ["user"]


class QuestionInline(admin.TabularInline):
    """
    Allows viewing/editing Questions directly inside the UnitSubtopic admin page.
    """

    model = Question
    extra = 0  # Don't show blank slots, just existing questions
    fields = ("serial_number", "short_content", "difficulty", "is_active", "is_verified")
    readonly_fields = ("short_content",)
    show_change_link = True  # Adds a link to edit the full question

    def short_content(self, obj):
        """Helper to truncate long question content in the inline."""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    short_content.short_description = "Content"


# --- MODEL ADMINS ---


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "year", "semester")
    search_fields = ("name", "code")
    list_filter = ("year", "semester")

    # From one Course page, you can manage all its Units and Enrolments.
    inlines = [UnitInline, EnrolmentInline]


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("name", "number", "course")
    search_fields = ("name", "course__name")
    list_filter = ("course__name",)
    autocomplete_fields = ["course"]

    inlines = [UnitSubtopicInline]


@admin.register(UnitSubtopic)
class UnitSubtopicAdmin(admin.ModelAdmin):
    list_display = ("name", "unit")
    search_fields = ("name", "unit__name")
    autocomplete_fields = ["unit"]
    
    inlines = [QuestionInline]


@admin.register(Enrolment)
class EnrolmentAdmin(admin.ModelAdmin):
    list_display = ("user", "course", "is_instructor")
    search_fields = ("user__username", "course__name")
    list_filter = ("is_instructor", "course__name")
    autocomplete_fields = ["user", "course"]


@admin.register(StudyAid)
class StudyAidAdmin(admin.ModelAdmin):
    list_display = ("name", "subtopic", "aid_type")
    search_fields = ("name", "subtopic__name", "aid_type__name")
    list_filter = ("aid_type__name",)
    autocomplete_fields = ["subtopic", "aid_type"]


@admin.register(AidType)
class AidTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)
