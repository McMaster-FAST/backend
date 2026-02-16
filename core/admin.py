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
    # Columns to show in the list view
    list_display = (
        "pk",
        "public_id",
        "serial_number",
        "short_content",
        "difficulty",
        "is_active",
        "is_verified",
    )
    # Search bar capabilities
    search_fields = ("serial_number", "content")
    # Sidebar filters
    list_filter = ("is_active", "is_verified", "difficulty")
    # Add the inline defined above
    inlines = [QuestionOptionInline]

    # Helper to truncate long text in the list view
    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content


@admin.register(QuestionGroup)
class QuestionGroupAdmin(admin.ModelAdmin):
    list_display = ("group_name",)
    search_fields = ("group_name",)
    filter_horizontal = ("questions",)  # Makes selecting many questions much easier


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
    list_display = ("user", "course", "subtopic", "current_question")
