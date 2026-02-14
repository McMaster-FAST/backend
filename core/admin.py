from django.contrib import admin
from .models import (
    SavedForLater,
    QuestionGroup,
    Question,
    QuestionComment,
    QuestionOption,
    QuestionImage,
    TestSession,
)


# --- INLINES ---
# This allows you to add/edit Options directly while editing a Question
class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 1  # Shows one blank slot for a new option by default


# --- MODEL ADMINS ---


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        "serial_number",
        "get_course",
        "get_subtopic",
        "short_content",
        "difficulty",
        "is_active",
        "is_verified",
    )

    list_filter = (
        "subtopic__unit__course",
        "is_active",
        "is_verified",
    )

    search_fields = ("serial_number", "content", "subtopic__name")

    autocomplete_fields = ["subtopic"]

    inlines = [QuestionOptionInline]

    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    # Displays the Subtopic Name, sorted by the subtopic name field
    @admin.display(ordering="subtopic__name", description="Subtopic")
    def get_subtopic(self, obj):
        return obj.subtopic.name if obj.subtopic else "-"

    # Displays the Course Code, sorted by the course code field
    @admin.display(ordering="subtopic__unit__course__code", description="Course")
    def get_course(self, obj):
        # We traverse: Question -> Subtopic -> Unit -> Course
        if obj.subtopic and obj.subtopic.unit and obj.subtopic.unit.course:
            return obj.subtopic.unit.course.code
        return "-"


@admin.register(QuestionGroup)
class QuestionGroupAdmin(admin.ModelAdmin):
    list_display = ("group_name",)
    search_fields = ("group_name",)
    filter_horizontal = ("questions",)


@admin.register(QuestionOption)
class QuestionOptionAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "content",
        "question",
        "is_answer",
        "selection_frequency",
    )
    list_filter = ("is_answer",)


@admin.register(QuestionComment)
class QuestionCommentAdmin(admin.ModelAdmin):
    list_display = ("public_id", "user", "question", "short_comment", "timestamp")

    def short_comment(self, obj):
        return obj.comment_text[:50]


@admin.register(SavedForLater)
class SavedForLaterAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "timestamp")


@admin.register(QuestionImage)
class QuestionImageAdmin(admin.ModelAdmin):
    list_display = ("id", "alt_text", "image_file")


@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ("user", "subtopic", "current_question", "difficulty_range")
