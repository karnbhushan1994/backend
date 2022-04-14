import uuid
from django.db import models
from ..models import TaggUser
from django.contrib.contenttypes.fields import GenericForeignKey, ContentType


class NotificationType(models.TextChoices):
    DEFAULT = "DFT"
    FRIEND_REQUEST = "FRD_REQ"
    FRIEND_ACCEPTANCE = "FRD_ACPT"
    COMMENT = "CMT"
    LINK_TAGGS = "LKT"
    MOMENT_3P = "MOM_3+"
    MOMENT_FRIEND = "MOM_FRIEND"
    INVITEE_ONBOARDED = "INVT_ONBRD"
    MOMENT_TAG = "MOM_TAG"
    SYSTEM_MSG = "SYSTEM_MSG"
    PROFILE_VIEW = "P_VIEW"
    MOMENT_VIEW = "M_VIEW"
    CLICK_TAG = "CLICK_TAG"


class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    verbage = models.CharField(max_length=255, default="")
    notification_type = models.CharField(
        max_length=10,
        choices=NotificationType.choices,
        default=NotificationType.DEFAULT,
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    notification_object = models.UUIDField(null=True)
    object = GenericForeignKey("content_type", "notification_object")
    timestamp = models.DateTimeField(auto_now_add=True)


class NotificationList(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE)
    user = models.ForeignKey(TaggUser, on_delete=models.CASCADE)

    class Meta:
        indexes = [models.Index(fields=["notification", "user"])]


class ProfileViewNotificationTrigger(models.Model):
    user = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)
