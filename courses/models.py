from django.db import models
from django.conf import settings
from core.models import QuestionGroup

# Create your models here.

class Course(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=10)
    year = models.IntegerField()
    semester = models.IntegerField()

    class Meta:
        unique_together = ('code', 'year', 'semester')

class Unit(models.Model):
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    name = models.TextField()
    number = models.IntegerField()
    class Meta:
        unique_together = ('course', 'name')

class UnitSubTopic(models.Model):
    unit = models.ForeignKey("Unit", on_delete=models.CASCADE)
    name = models.TextField()
    question_group = models.ForeignKey(QuestionGroup, on_delete=models.CASCADE)
    class Meta:
        unique_together = ('unit', 'name')

class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    is_instructor = models.BooleanField(default=False)
    class Meta:
        unique_together = ('user', 'course')