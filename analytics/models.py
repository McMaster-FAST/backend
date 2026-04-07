from django.db import models
from django.conf import settings
from django.utils.functional import cached_property

from courses.models import Course


class QuestionAttempt(models.Model):
    question = models.ForeignKey("core.Question", on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    answered_correctly = models.BooleanField()
    skipped = models.BooleanField(default=False)
    updated_ability_score = models.DecimalField(
        max_digits=5, decimal_places=4, default=0
    )
    time_spent = models.FloatField()

    class Meta:
        unique_together = ("user", "question", "timestamp")
        verbose_name = "Question Attempt"
        verbose_name_plural = "Question Attempts"

    def __str__(self):
        return f"{self.user.username} - {self.question} at {self.timestamp}"


class UserTopicAbilityScore(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    unit_sub_topic = models.ForeignKey("courses.UnitSubtopic", on_delete=models.CASCADE)
    # Default to average ability with high uncertainty
    variance = models.DecimalField(max_digits=6, decimal_places=4, default=10.000)
    score = models.DecimalField(max_digits=5, decimal_places=4, default=0.00)

    class Meta:
        unique_together = ("user", "unit_sub_topic")
        verbose_name = "User Topic Ability Score"
        verbose_name_plural = "User Topic Ability Scores"

    def __str__(self):
        return f"{self.user.username} - {self.unit_sub_topic} - {self.score}"


class CourseXP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="course_xps"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="student_xps"
    )
    total_xp = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = (
            "user",
            "course",
        )

        verbose_name = "Course XP"
        verbose_name_plural = "Course XP"

    @cached_property
    def _xp_calculations(self):
        """
        Calculates the user's level based on a doubling XP requirement.
        Level 1 requires 100 XP to complete. Level 2 requires 200. Level 3 requires 400, etc.
        """
        level = 1
        threshold = 100  # Base XP needed to reach Level 2
        remaining_xp = self.total_xp

        # Keep leveling up the user as long as they have enough XP to pass the current threshold
        while remaining_xp >= threshold:
            remaining_xp -= threshold
            level += 1
            threshold *= 2  # Double the requirement for the next level!

        return {
            "level": level,
            "xp_in_current_level": remaining_xp,
            "xp_for_next_level": threshold,
            "progress_percentage": int((remaining_xp / threshold) * 100),
        }

    @property
    def level(self):
        return self._xp_calculations["level"]

    @property
    def xp_in_current_level(self):
        return self._xp_calculations["xp_in_current_level"]

    @property
    def xp_for_next_level(self):
        return self._xp_calculations["xp_for_next_level"]

    @property
    def progress_percentage(self):
        return self._xp_calculations["progress_percentage"]
