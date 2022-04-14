import uuid

from django.db import models

from ...models import TaggUser
from ..models import Moment


class MomentTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    x = models.FloatField(blank=True, default=0)
    y = models.FloatField(blank=True, default=0)
    z = models.IntegerField(blank=True, default=0)

    class Meta:
        indexes = [
            models.Index(fields=["id"]),
        ]


class MomentTagList(models.Model):
    moment_tag = models.ForeignKey(MomentTag, on_delete=models.CASCADE)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE)

    class Meta:
        models.Index(fields=["moment_tagg", "moment"])
