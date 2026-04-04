import uuid

from django.db import models


class UUIDModel(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        abstract = True
