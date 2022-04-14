import logging

from django.core.cache import cache
from rest_framework import serializers

from ...moments.models import Moment
from ...widget.models import (
    ApplicationLinkWidget,
    GenericLinkWidget,
    SocialMediaWidget,
    VideoLinkWidget,
    Widget,
    WidgetType,
)
from ...widget.serializers import WidgetSerializer

logger = logging.getLogger(__name__)


class WidgetViewsSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()
    link_type = serializers.SerializerMethodField()
    views = serializers.SerializerMethodField()
    widget_id = serializers.SerializerMethodField()

    def get_views(self, obj):
        return obj["views"]

    def get_link_type(self, obj):
        widget = Widget.objects.filter(id=obj["widget"]).select_subclasses()[0]
        if (
            isinstance(widget, VideoLinkWidget)
            or isinstance(widget, ApplicationLinkWidget)
            or isinstance(widget, GenericLinkWidget)
            or isinstance(widget, SocialMediaWidget)
        ):
            return widget.link_type
        else:
            logger.error(f"Found an invalid widget type: {widget.id}")
            return ""

    def get_widget_id(self, obj):
        widget = Widget.objects.filter(id=obj["widget"]).select_subclasses()[0]
        return widget.id

    def get_title(self, obj):
        widget = Widget.objects.filter(id=obj["widget"]).select_subclasses()[0]

        if (
            isinstance(widget, VideoLinkWidget)
            or isinstance(widget, ApplicationLinkWidget)
            or isinstance(widget, GenericLinkWidget)
        ):
            return widget.title
        elif isinstance(widget, SocialMediaWidget):
            return widget.username
        else:
            logger.error(f"Found an invalid widget type: {widget.id}")
            return ""
