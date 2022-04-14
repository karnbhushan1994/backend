from enum import Enum
from django.db import models
from ...models import TaggUser
from ...moments.models import Moment


class MomentShares(models.Model):
    moment_shared = models.ForeignKey(
        Moment, related_name="moment_shared", on_delete=models.CASCADE
    )
    moment_sharer = models.ForeignKey(
        TaggUser, related_name="moment_sharer", on_delete=models.SET_NULL, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["moment_shared", "timestamp"])]
