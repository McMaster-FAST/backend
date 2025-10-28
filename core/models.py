from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    # Typical user fields are in AbstractUser
    ability_score = models.FloatField(default=0)

class SavedForLater(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    timestamp = models.DateTimeField()

class Course(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    year = models.IntegerField()
    semester = models.IntegerField()

    class Meta:
        unique_together = ('code', 'year', 'semester')

class Enrollment(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    is_instructor = models.BooleanField(default=False)
    class Meta:
        unique_together = ('user', 'course')

class QuestionGroup(models.Model):
    group_name = models.TextField()
    questions = models.ManyToManyField("Question")

class Unit(models.Model):
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    name = models.TextField()
    question_group = models.ForeignKey("QuestionGroup", on_delete=models.CASCADE)
    class Meta:
        unique_together = ('course', 'name')

class Question(models.Model):
    serial_number = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    difficulty = models.FloatField()
    is_flagged = models.BooleanField(default=False)

class QuestionComment(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    comment_text = models.TextField()
    timestamp = models.DateTimeField()

class QuestionAnalytics(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    answered_correctly = models.BooleanField()
    updated_ability_score = models.FloatField()
    time_spent = models.FloatField()

class QuestionOption(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    content = models.TextField()
    is_answer = models.BooleanField(default=False)
