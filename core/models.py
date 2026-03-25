from django.db import models
from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from MacFAST.models import UUIDModel

# Create your models here.


class SavedForLater(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "question")
        verbose_name = "Question Saved For Later"
        verbose_name_plural = "Questions Saved For Later"

    def __str__(self):
        return f"{self.user} - {self.question}"


class QuestionGroup(UUIDModel):
    group_name = models.TextField(unique=True)
    questions = models.ManyToManyField("Question")

    class Meta:
        verbose_name = "Question Group"
        verbose_name_plural = "Question Groups"

    def __str__(self):
        return self.group_name


class Question(UUIDModel):
    subtopic = models.ForeignKey(
        "courses.UnitSubtopic", on_delete=models.CASCADE, null=True
    )
    serial_number = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    answer_explanation = models.TextField(blank=True)

    selection_frequency = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    discrimination = models.DecimalField(max_digits=5, decimal_places=4, default=1)
    difficulty = models.DecimalField(max_digits=5, decimal_places=4, default=0)
    guessing = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    is_flagged = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    images = models.ManyToManyField("QuestionImage", blank=True)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"

    def __str__(self):
        return f"{self.serial_number}"


class QuestionComment(UUIDModel):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    comment_text = models.TextField()
    reply_to = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Question Comment"
        verbose_name_plural = "Question Comments"

    def __str__(self):
        return f"{self.user} on {self.question}"


class QuestionOption(UUIDModel):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    content = models.TextField()
    is_answer = models.BooleanField(default=False)
    selection_frequency = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    images = models.ManyToManyField("QuestionImage", blank=True)

    class Meta:
        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"

    def __str__(self):
        return f"Option for {self.question}"


class QuestionImage(UUIDModel):
    image_file = models.ImageField(upload_to="question_images/", unique=True)
    alt_text = models.TextField(blank=True)

    class Meta:
        verbose_name = "Question Image"
        verbose_name_plural = "Question Images"

    def __str__(self):
        return f"{self.alt_text}"


@receiver(pre_delete, sender=QuestionImage)
def question_image_delete(sender, instance, **kwargs):
    instance.image_file.delete(False)


class TestSession(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subtopic = models.ForeignKey(
        "courses.UnitSubtopic", on_delete=models.CASCADE, null=True
    )
    # The window that we can pick questions from for this user.
    selection_upper_bound = models.FloatField(default=0.5)
    selection_lower_bound = models.FloatField(default=-0.5)
    has_seen_stop_message = models.BooleanField(default=False)
    questions_answered_count = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Test Session"
        verbose_name_plural = "Test Sessions"

    def __str__(self):
        return f"Test Session for {self.user} in {self.subtopic}"


class AdaptiveTestQuestionMetric(UUIDModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    # Corresponds to the number of questions asked in TestSession. Used to determine if we can show this skipped question yet.
    skipped_at_index = models.IntegerField(null=True, blank=True)
    skips_since_last_answer = models.IntegerField(default=0)
    total_times_seen = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Adaptive Test Question Metric"
        verbose_name_plural = "Adaptive Test Question Metrics"
        unique_together = ("user", "question")

    def __str__(self):
        return f"{self.question} seen by {self.user}"


class TestingParameters(UUIDModel):
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)

    # How many questions to use MAP for before switch to MLE
    warmpup_length = models.IntegerField(default=3)
    skip_readmit_delay = models.IntegerField(default=5)
    max_skips = models.IntegerField(default=3)
    max_question_repetitions = models.IntegerField(default=3)
    min_questions_between_repitions = models.IntegerField(default=5)
    # The variance at which the user should probably stop practicing and move on to the next subtopic.
    suggested_stopping_threshold = models.FloatField(default=0.8)
    window_increment = models.FloatField(default=0.25)

    class Meta:
        verbose_name = "Testing Parameters"
        verbose_name_plural = "Testing Parameters"

    @staticmethod
    def get_cache_name(course_id: str):
        return f"test_parameters_{course_id}"


class CourseResumeState(UUIDModel):
    # Tracks the last studied subtopic for a given user and course.

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey("courses.Course", on_delete=models.CASCADE)
    last_subtopic = models.ForeignKey("courses.UnitSubtopic", on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Course Resume State"
        verbose_name_plural = "Course Resume States"
        unique_together = ("user", "course")

    def __str__(self):
        return f"{self.user} - {self.course} -> {self.last_subtopic}"
