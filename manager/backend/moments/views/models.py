from django.db import models
from ...models import TaggUser
from ...moments.models import Moment


class MomentViews(models.Model):
    moment_viewed = models.ForeignKey(
        Moment, related_name="moment_viewed", on_delete=models.SET_NULL, null=True
    )
    moment_viewer = models.ForeignKey(
        TaggUser, related_name="moment_viewer", on_delete=models.SET_NULL, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["moment_viewed", "timestamp"])]
