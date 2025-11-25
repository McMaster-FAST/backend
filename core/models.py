from django.db import models
from django.conf import settings

# Create your models here.


class SavedForLater(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "question")
        verbose_name = "Question Saved For Later"
        verbose_name_plural = "Questions Saved For Later"

    def __str__(self):
        return f"{self.user} - {self.question}"


class QuestionGroup(models.Model):
    group_name = models.TextField(unique=True)
    questions = models.ManyToManyField("Question")

    class Meta:
        verbose_name = "Question Group"
        verbose_name_plural = "Question Groups"

    def __str__(self):
        return self.group_name


class Question(models.Model):
    subtopic = models.ForeignKey(
        "courses.UnitSubtopic", on_delete=models.CASCADE, null=True
    )
    serial_number = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    answer_explanation = models.TextField(blank=True)

    selection_frequency = models.DecimalField(max_digits=5, decimal_places=4, default=0)

    discrimination = models.DecimalField(max_digits=5, decimal_places=4, default=0)
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


class QuestionComment(models.Model):
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


class QuestionOption(models.Model):
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


class QuestionImage(models.Model):
    image_file = models.ImageField(upload_to="question_images/", unique=True)
    alt_text = models.TextField(blank=True)

    class Meta:
        verbose_name = "Question Image"
        verbose_name_plural = "Question Images"

    def __str__(self):
        return f"{self.alt_text}"
