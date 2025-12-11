from django.db import models
from django.conf import settings

# Create your models here.


class Course(models.Model):
    class SemesterChoices(models.TextChoices):
        FALL = "FALL", "Fall"
        WINTER = "WINTER", "Winter"
        SPRING = "SPRING", "Spring"
        SUMMER = "SUMMER", "Summer"
        MULTI_TERM = "MULTI_TERM", "Multi-term"

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=15)
    description = models.TextField(blank=True)
    year = models.IntegerField()
    semester = models.CharField(choices=SemesterChoices.choices, max_length=20)
    is_archived = models.BooleanField(default=False)

    class Meta:
        unique_together = ("code", "year", "semester")
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return f"{self.code} - ({self.year} {self.semester})"


class Unit(models.Model):
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    number = models.IntegerField()

    class Meta:
        unique_together = ("course", "name")
        verbose_name = "Unit"
        verbose_name_plural = "Units"

    def __str__(self):
        return f"{self.course.code} - {self.name}"


class UnitSubtopic(models.Model):
    unit = models.ForeignKey("Unit", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("unit", "name")
        verbose_name = "Unit Subtopic"
        verbose_name_plural = "Unit Subtopics"

    def __str__(self):
        return f"{self.unit.course.code} - {self.unit.name} - {self.name}"


class AidType(models.Model):
    """
    Restrict Study Aids to specific types (e.g., Video, PDF, Download).
    """

    class AidTypeChoices(models.TextChoices):
        PDF = "PDF", "PDF Document"
        VIDEO = "VIDEO", "Video Tutorial"
        LINK = "LINK", "External Link"
        AUDIO = "AUDIO", "Audio Recording"

    name = models.CharField(max_length=50, choices=AidTypeChoices.choices, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = "Aid Type"
        verbose_name_plural = "Aid Types"

    def __str__(self):
        return self.get_name_display()


class StudyAid(models.Model):
    subtopic = models.ForeignKey("UnitSubtopic", on_delete=models.CASCADE)
    aid_type = models.ForeignKey("AidType", on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    reference = models.TextField()

    class Meta:
        verbose_name = "Study Aid"
        verbose_name_plural = "Study Aids"

    def __str__(self):
        return f"{self.subtopic.unit.course.code} - {self.subtopic.name} - {self.name}"


class Enrolment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    is_instructor = models.BooleanField(default=False)
    is_ta = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "course")
        verbose_name = "Enrolment"
        verbose_name_plural = "Enrolments"

    def __str__(self):
        return f"{self.user.username} - {self.course.code}"
