from django.db import models
from django.conf import settings


class QuestionAttempt(models.Model):
    question = models.ForeignKey("core.Question", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    answered_correctly = models.BooleanField()
    updated_ability_score = models.DecimalField(
        max_digits=5, decimal_places=4, default=0
    )
    time_spent = models.FloatField()

    class Meta:
        verbose_name = "Question Attempt"
        verbose_name_plural = "Question Attempts"

    def __str__(self):
        return f"{self.user.username} - {self.question} at {self.timestamp}"


class UserTopicAbilityScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    unit_sub_topic = models.ForeignKey("courses.UnitSubtopic", on_delete=models.CASCADE)
    score = models.DecimalField(max_digits=5, decimal_places=4, default=0.00)

    class Meta:
        unique_together = ("user", "unit_sub_topic")
        verbose_name = "User Topic Ability Score"
        verbose_name_plural = "User Topic Ability Scores"

    def __str__(self):
        return f"{self.user.username} - {self.unit_sub_topic} - {self.score}"
