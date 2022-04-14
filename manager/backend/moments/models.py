from enum import Enum
import uuid
from django.db import models

from ..models import TaggUser
from django.contrib.contenttypes.fields import GenericRelation
from ..notifications.models import Notification


class Moment(models.Model):
    moment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Many to one : user -> moment (A user can have many moments)
    user_id = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    caption = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    moment_url = models.CharField(max_length=256)
    thumbnail_url = models.CharField(max_length=256)
    resource_path = models.CharField(max_length=256, default="")
    moment_category = models.CharField(max_length=128)
    view_count = models.IntegerField(default=0)
    share_count = models.IntegerField(default=0)
    notifications = GenericRelation(Notification, object_id_field="notification_object")
    updated_on = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        indexes = [models.Index(fields=["moment_id"]), models.Index(fields=["user_id"])]


class MomentEngagement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)
    view_duration = models.IntegerField(default=0)
    clicked_on_profile = models.BooleanField(default=False)
    clicked_on_comments = models.BooleanField(default=False)
    clicked_on_share = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["user"])]
        unique_together = ("user", "moment")


class MomentScoreWeights(Enum):
    VIEW = 0.7
    COMMENT = 0.2
    SHARE = 0.1
    MOMENTVIEW = 10 #to increase moment score by 10 for every 50 views on a moment

class MomentScores(models.Model):
    moment = models.ForeignKey(Moment, related_name="moment", on_delete=models.CASCADE)
    score = models.DecimalField(default=0, decimal_places=4, max_digits=46)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["moment", "timestamp"])]

class DailyMoment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    moment = models.ForeignKey(Moment, on_delete=models.CASCADE)
    date = models.DateField()
    status = models.BooleanField(default=False)
    owner_id=models.ForeignKey(TaggUser,related_name='%(class)s_owner_id',on_delete=models.CASCADE,null=True)
