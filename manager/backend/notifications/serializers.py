from rest_framework import serializers

from ..moments.models import Moment
from ..moments.comments.models import CommentThreads, MomentComments
from ..moments.comments.serializers import (
    CommentNotificationSerializer,
    ThreadNotificationSerializer,
)
from ..serializers import TaggUserSerializer
from ..moments.serializers import MomentSerializer
from .models import Notification, NotificationList


class NotificationSerializer(serializers.ModelSerializer):
    notification_object = serializers.SerializerMethodField()
    actor = TaggUserSerializer()

    class Meta:
        model = Notification
        fields = "__all__"

    def get_notification_object(self, obj):
        if isinstance(obj.object, MomentComments):
            return CommentNotificationSerializer(obj.object).data
        elif isinstance(obj.object, CommentThreads):
            return ThreadNotificationSerializer(obj.object).data
        elif isinstance(obj.object, Moment):
            return MomentSerializer(obj.object).data


class NotificationListSerializer(serializers.ModelSerializer):
    notification = NotificationSerializer()

    class Meta:
        model = NotificationList
        fields = "__all__"
