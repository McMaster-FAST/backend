from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class MacFastUser(AbstractUser):
    # Typical user fields are in AbstractUser
    ability_score = models.DecimalField(max_digits=5, decimal_places=4, default=0.50)