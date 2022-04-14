import uuid

from django.db import models

from ..models import Moment, TaggUser
from ...notifications.models import Notification
from django.contrib.contenttypes.fields import GenericRelation


class MomentComments(models.Model):
    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Many to one : moment -> comment (A moment can have many comments)
    moment_id = models.ForeignKey(Moment, on_delete=models.CASCADE)
    commenter = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    comment = models.CharField(max_length=1024)
    date_created = models.DateTimeField(auto_now_add=True)

    notifications = GenericRelation(Notification, object_id_field="notification_object")

    class Meta:
        indexes = [
            models.Index(fields=["moment_id"]),
            models.Index(fields=["comment_id"]),
        ]

class NewCommentStatus(models.Model):
    NewComment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commenter = models.OneToOneField(TaggUser, on_delete=models.CASCADE)
    flag = models.BooleanField()


class CommentThreads(models.Model):

    comment_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    commenter = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    comment = models.CharField(max_length=256)
    date_created = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey(MomentComments, on_delete=models.CASCADE)
    notifications = GenericRelation(Notification, object_id_field='notification_object')

    class Meta:
        indexes = [
            models.Index(fields=["parent_comment"]),
            models.Index(fields=["comment_id"]),
        ]
