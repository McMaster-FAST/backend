from django.db import models
from django.contrib.auth.models import AbstractUser
from courses.models import UnitSubtopic


# Create your models here.
class MacFastUser(AbstractUser):
    active_subtopic = models.ForeignKey(
        UnitSubtopic, default=None, null=True, on_delete=models.SET_DEFAULT
    )
