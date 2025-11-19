from django.db import models
from django.conf import settings

# Create your models here.


class SavedForLater(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)


class QuestionGroup(models.Model):
    group_name = models.TextField(unique=True)
    questions = models.ManyToManyField("Question")


class Question(models.Model):
    serial_number = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    difficulty = models.DecimalField(max_digits=3, decimal_places=2, default=0.50)
    is_flagged = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    images = models.ManyToManyField("QuestionImage", blank=True)


class QuestionComment(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    comment_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)


class QuestionAnalytics(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    answered_correctly = models.BooleanField()
    updated_ability_score = models.FloatField()
    time_spent = models.FloatField()


class QuestionOption(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    content = models.TextField()
    is_answer = models.BooleanField(default=False)
    selection_frequency = models.FloatField(default=0)
    images = models.ManyToManyField("QuestionImage", blank=True)


class QuestionImage(models.Model):
    image_file = models.ImageField(upload_to="question_images/")
    alt_text = models.TextField(blank=True)
