from django.db import models
import uuid

class UUIDModel(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True