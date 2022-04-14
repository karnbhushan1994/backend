import logging

from rest_framework import serializers

from ..serializers import TaggUserSerializer
from .models import (
    ApplicationLinkWidget,
    GenericLinkWidget,
    SocialMediaWidget,
    VideoLinkWidget,
    Widget,
)

logger = logging.getLogger(__name__)


class WidgetSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        if isinstance(instance, VideoLinkWidget):
            return VideoLinkWidgetSerializer(instance=instance).data
        if isinstance(instance, ApplicationLinkWidget):
            return ApplicationLinkWidgetSerializer(instance=instance).data
        if isinstance(instance, GenericLinkWidget):
            return GenericLinkWidgetSerializer(instance=instance).data
        elif isinstance(instance, SocialMediaWidget):
            return SocialMediaWidgetSerializer(instance=instance).data
        else:
            logger.error(f"Found an invalid widget type: {instance.id}")
            return {}

    class Meta:
        model = Widget
        fields = "__all__"


class WidgetBaseSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["owner"] = TaggUserSerializer(instance.owner).data
        return rep


class VideoLinkWidgetSerializer(WidgetBaseSerializer, serializers.ModelSerializer):
    class Meta:
        model = VideoLinkWidget
        fields = "__all__"


class ApplicationLinkWidgetSerializer(
    WidgetBaseSerializer, serializers.ModelSerializer
):
    class Meta:
        model = ApplicationLinkWidget
        fields = "__all__"


class GenericLinkWidgetSerializer(WidgetBaseSerializer, serializers.ModelSerializer):
    class Meta:
        model = GenericLinkWidget
        fields = "__all__"


class SocialMediaWidgetSerializer(WidgetBaseSerializer, serializers.ModelSerializer):
    class Meta:
        model = SocialMediaWidget
        fields = "__all__"
