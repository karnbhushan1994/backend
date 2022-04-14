import logging
from random import shuffle

from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..widget.models import ApplicationLinkWidgetType, VideoLinkWidgetType, WidgetType
from .utils import get_top_taggs


class TaggShopViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @method_decorator(cache_page(6 * 60 * 60))
    @action(detail=False, methods=["get"])
    def top_taggs_today(self, request):
        return Response(get_top_taggs())

    @method_decorator(cache_page(6 * 60 * 60))
    @action(detail=False, methods=["get"])
    def available_taggs(self, request):
        # TODO just returning all taggs now
        all_taggs = (
            list(WidgetType)
            + list(VideoLinkWidgetType)
            + list(ApplicationLinkWidgetType)
        )
        all_taggs.remove(WidgetType.VIDEO_LINK)
        all_taggs.remove(WidgetType.APPLICATION_LINK)
        shuffle(all_taggs)
        return Response(all_taggs)
