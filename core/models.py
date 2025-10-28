from django.db import models

class User(models.Model):
    # TODO: Anything for auth later?
    username = models.TextField(unique=True)
    email = models.EmailField(unique=True)
    ability_score = models.FloatField(default=0)
    is_admin = models.BooleanField(default=False)

class SavedForLater(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class Course(models.Model):
    name = models.TextField()
    code = models.CharField(max_length=10)
    year = models.IntegerField()
    semester = models.IntegerField()

    class Meta:
        unique_together = ('code', 'year', 'semester')

class Enrollment(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)

class InstructorAssignment(models.Model):
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    course = models.ForeignKey("Course", on_delete=models.CASCADE)

class Unit(models.Model):
    course = models.ForeignKey("Course", on_delete=models.CASCADE)
    name = models.TextField()
    question_group = models.ForeignKey("QuestionGroup", on_delete=models.CASCADE)
    class Meta:
        unique_together = ('course', 'name')

class QuestionGroup(models.Model):
    group_name = models.TextField()
    question_id = models.ManyToManyField("Question", on_delete=models.CASCADE)

class Question(models.Model):
    serial_number = models.CharField(max_length=255, unique=True)
    content = models.TextField()
    difficulty = models.FloatField()
    is_flagged = models.BooleanField(default=False)

class QuestionComment(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    comment_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

class QuestionAnalytics(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    user = models.ForeignKey("User", on_delete=models.CASCADE)
    answered_correctly = models.BooleanField()
    updated_ability_score = models.FloatField()
    time_spent = models.FloatField(default=0.0)

class QuestionOption(models.Model):
    question = models.ForeignKey("Question", on_delete=models.CASCADE)
    content = models.TextField()
    is_answer = models.BooleanField(default=False)
