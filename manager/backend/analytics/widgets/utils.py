import logging
import random
from datetime import datetime

import pytz
from django.db.models import Count

from ...widget.models import RewardCalculation
from ...gamification.constants import TAGG_SCORE_ALLOTMENT
from ...gamification.utils import increase_tagg_score

from ...notifications.models import (
    NotificationType,
)

from ...common.notification_manager import handle_notification

from ..utils import get_start_day_for_applied_filter

from .models import WidgetViews


def record_widget_click(widget, viewer):
    """
    To record a click on the given widget by a given user
    """
    try:
        count = random.randint(2, 5)
        for _ in range(count):
            WidgetViews.objects.create(
                widget=widget,
                viewer=viewer,
                timestamp=pytz.UTC.localize(datetime.now()),
            )

        send_tagg_click_count_notification(widget, count)
    except Exception:
        raise Exception


def send_tagg_click_count_notification(widget, count):
    if RewardCalculation.objects.filter(userId=widget.owner).exists():
        view_count = RewardCalculation.objects.filter(userId=widget.owner)[0]

        new_count = view_count.count + count
        if new_count > 30:
            handle_notification(
                notification_type=NotificationType.CLICK_TAG,
                actor=widget.owner,
                receiver=widget.owner,
                verbage="Your Taggs are getting clicked! Here's some Tagg coin!",
                notification_object=None,
            )
            increase_tagg_score(
                widget.owner, TAGG_SCORE_ALLOTMENT["TAGG_CLICK_COUNT_10"]
            )
            new_count = 0
        view_count.count = new_count
        view_count.save()
    else:
        RewardCalculation.objects.create(
            taggId=widget, userId=widget.owner, count=count
        )


def get_total_widget_view_count(user, filter_type):
    """
    To retrieve total clicks a given user has received
    according to the applied filter
    """
    try:
        lowerbound = get_start_day_for_applied_filter(filter_type)

        if not WidgetViews.objects.filter(
            widget__owner=user,
            timestamp__gte=lowerbound,
            timestamp__lte=pytz.UTC.localize(datetime.now()),
        ).exists():
            return 0

        views = WidgetViews.objects.filter(
            widget__owner=user,
            timestamp__gte=lowerbound,
            timestamp__lte=pytz.UTC.localize(datetime.now()),
        ).count()

        return views
    except Exception as err:
        logging.exception(
            "There was a problem while getting the total widget views count ", err
        )
        raise Exception


def get_top_widget(user, filter_type):
    """
    To retrieve top tagg for a given user according to the applied filter
    """
    try:
        lowerbound = get_start_day_for_applied_filter(filter_type)

        if not WidgetViews.objects.filter(
            widget__owner=user,
            timestamp__gte=lowerbound,
            timestamp__lte=pytz.UTC.localize(datetime.now()),
        ).exists():
            return None

        top_tagg = (
            WidgetViews.objects.filter(
                widget__owner=user,
                timestamp__gte=lowerbound,
                timestamp__lte=pytz.UTC.localize(datetime.now()),
            )
            .values("widget")
            .annotate(views=Count("widget"))
            .latest("views")
        )

        return top_tagg
    except Exception as err:
        logging.exception(
            "There was a problem while getting the total widget views count ", err
        )
        raise Exception


def get_widget_view_distribution_by_widget(user, filter_type):
    """
    To retrieve clicks distribution across user's taggs
    for a given user according to the applied filter
    """
    try:
        lowerbound = get_start_day_for_applied_filter(filter_type)
        distribution = (
            WidgetViews.objects.filter(
                widget__owner=user,
                timestamp__gte=lowerbound,
                timestamp__lte=pytz.UTC.localize(datetime.now()),
            )
            .values("widget")
            .annotate(views=Count("widget"))
            .order_by("-views")
        )

        return distribution
    except Exception as err:
        logging.exception(
            "There was a problem while getting the widget view distribution per widget",
            err,
        )
        raise Exception
