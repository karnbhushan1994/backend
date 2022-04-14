import logging
import random
from datetime import datetime, timedelta

import pytz
from django.utils.timezone import localtime
from ...analytics.widgets.models import WidgetViews
from ...common.notification_manager import handle_notification
from ...gamification.constants import TAGG_SCORE_ALLOTMENT
from ...gamification.utils import increase_tagg_score

from ...notifications.models import (
    NotificationType,
    ProfileViewNotificationTrigger,
)

from ..utils import (
    get_start_day_for_applied_filter,
    get_timeperiod_for_distribution_by_filter_type,
)

from .models import ProfileViews, ProfileVisits

logger = logging.getLogger(__name__)


def record_profile_click(user, visitor):
    """
    To record a click on a given profile by a given user
    """
    try:

        count = random.randint(1, 5)
        for _ in range(count):
            ProfileViews.objects.create(
                profile_visited=user,
                profile_visitor=visitor,
                timestamp=pytz.UTC.localize(datetime.now()),
            )
        send_profile_view_count_notification(user, count)

    except Exception as err:
        logger.error(
            "There was a problem while trying to record a click ",
            err,
        )
        raise Exception


def send_profile_view_count_notification(user, count):
    if ProfileViewNotificationTrigger.objects.filter(user=user).exists():
        view_count = ProfileViewNotificationTrigger.objects.filter(user=user)[0]

        new_count = view_count.count + count
        if new_count > 15:
            handle_notification(
                notification_type=NotificationType.PROFILE_VIEW,
                actor=user,
                receiver=user,
                verbage="Your profile is getting viewed! You've been rewarded with some Tagg coin!",
                notification_object=None,
            )
            increase_tagg_score(user, TAGG_SCORE_ALLOTMENT["PROFILE_CLICK_COUNT_5"])
            new_count = 0
        view_count.count = new_count
        view_count.save()
    else:
        ProfileViewNotificationTrigger.objects.create(user=user, count=count)


def get_profile_view_distribution_by_day(user, day):
    """
    Function to retrieve the profile view count on a given day
    Args:
        day: number of days ago from now()

    Returns: int number of profile views on that day
    """
    try:
        now_start_of_day = localtime(pytz.UTC.localize(datetime.now())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        local_lowerbound = now_start_of_day - timedelta(days=day)
        local_upperbound = localtime(local_lowerbound).replace(
            hour=23, minute=59, second=59
        )

        return ProfileViews.objects.filter(
            profile_visited=user,
            timestamp__gte=local_lowerbound,
            timestamp__lte=local_upperbound,
        ).count()

    except Exception as err:
        logging.exception(
            "There was a problem while getting the profile view count for a particular day ",
            err,
        )
        raise Exception


def get_profile_view_distribution_graph_data(user, filter_type):
    """
    To retrieve the profile view distribution count for a specific profile accrding to the filter type

    Args:
        filter_type: int/string
        Refer to SUPPORTED_FILTER_TYPES in analytics/common.py for list of valid inputs

    Returns: values[] containing the views for everyday within the applied filter
    """
    try:
        return {
            "values": get_profile_views_distribution_list_by_filter(user, filter_type),
            "labels": get_graph_labels_by_filter(filter_type),
        }

    except Exception as err:
        logging.exception(
            "There was a problem while getting the profile view count for specified filter type ",
            err,
        )
        raise Exception


def get_graph_labels_by_filter(filter_type):
    try:
        labels = []

        timeperiod = get_timeperiod_for_distribution_by_filter_type(filter_type)
        for day in range(filter_type - 1, -1, -(timeperiod)):
            timestamp = localtime(pytz.UTC.localize(datetime.now())) - timedelta(
                days=day
            )
            labels.append(timestamp)

        return labels
    except Exception as err:
        logging.exception(
            "There was a problem while getting graph labels for profile views ", err
        )
        raise Exception


def get_profile_views_distribution_list_by_filter(user, filter_type):
    """
    To retrieve the profile view distribution count for a specific profile accrding to the filter type

    Args:
        filter_type: int/string
        Refer to SUPPORTED_FILTER_TYPES in analytics/common.py for list of valid inputs

    Returns: values[] containing the views for everyday within the applied filter
    """
    try:
        values = []

        if isinstance(filter_type, str):
            return []

        for day in range(filter_type - 1, -1, -1):
            values.append(get_profile_view_distribution_by_day(user, day))

        return values
    except Exception as err:
        logging.exception(
            "There was a problem while getting the profile view count for specified filter type ",
            err,
        )
        raise Exception


def get_total_profile_view_count(user, filter_type):
    """
    To retrieve total clicks a given profile has received
    according to the applied filter

    Args:
        filter_type: int/string
        Refer to SUPPORTED_FILTER_TYPES in analytics/common.py for list of valid inputs

    Returns: int (count of views)
    """
    try:
        old_views = 0
        if ProfileVisits.objects.filter(user=user).exists() and (
            (isinstance(filter_type, str) and filter_type == "LIFETIME")
            or (isinstance(filter_type, int) and filter_type == 30)
        ):
            pv = ProfileVisits.objects.filter(user=user)[0]
            old_views = len(pv.visitors.split(","))

        lowerbound = get_start_day_for_applied_filter(filter_type)
        views = (
            ProfileViews.objects.filter(
                profile_visited=user,
                timestamp__gte=lowerbound,
                timestamp__lte=pytz.UTC.localize(datetime.now()),
            ).count()
            # + old_views
        )

        return views
    except Exception as err:
        logging.exception(
            "There was a problem while getting the total profile views count for specified filter type",
            err,
        )
        raise Exception
