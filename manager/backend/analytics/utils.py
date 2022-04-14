import logging
from datetime import datetime, timedelta

import pytz
from django.utils.timezone import localtime

from ..analytics.constants import SUPPORTED_FILTER_TYPES
from ..common.exception_handling.exception_classes import MissingParameterException
from ..common.validator import FieldException, check_is_valid_parameter
from .widgets.models import WidgetViews
from django.db.models import Count


def validate_filter_type_in_request(request):
    """
    To ensure filter_type is of the right format as part of the query params
    """
    data = request.query_params
    if not check_is_valid_parameter("filter_type", data):
        raise MissingParameterException

    filter_type = data.get("filter_type")
    filter_type = int(filter_type) if filter_type.isnumeric() else filter_type
    if filter_type in SUPPORTED_FILTER_TYPES:
        return True
    else:
        raise FieldException


def get_normalized_filter(filter_type):
    return int(filter_type) if filter_type.isnumeric() else filter_type


def get_start_day_for_applied_filter(filter_type):
    """
    To get the timestamp of the first day according to the filter type
    Eg: if current date is Jan 7th applied filter is last 7 days,
        function will return Jan 1st 00:00:00
    """
    try:
        lowerbound = None

        if isinstance(filter_type, int):
            lowerbound = pytz.UTC.localize(datetime.now() - timedelta(days=filter_type))

        elif isinstance(filter_type, str) and filter_type == "LIFETIME":
            lowerbound = pytz.UTC.localize(datetime(1000, 1, 1))

        lowerbound = localtime(lowerbound).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        return lowerbound

    except Exception as err:
        logging.exception(
            "There was a problem while getting the start date by filter type ", err
        )
        raise Exception


def get_timeperiod_for_distribution_by_filter_type(filter_type):
    """
    Get time period based on which the view distribution is built
    """
    try:
        if isinstance(filter_type, str):
            return 7

        if isinstance(filter_type, int):
            if filter_type == 30:
                return 7
            elif filter_type == 14:
                return 2
            else:
                return 1
    except Exception as err:
        logging.exception(
            "There was a problem while getting the timeperiod for profile view distribution date ",
            err,
        )
        raise Exception


def get_total_widget_view_count(user, filter_type):
    """
    To retrieve total clicks a given user has received
    according to the applied filter
    """
    try:
        lowerbound = get_start_day_for_applied_filter(filter_type)
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
        top_tagg = (
            WidgetViews.objects.filter(
                widget__active=True,
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


# count = random.randint(2, 5)
#         for _ in range(count):
#             WidgetViews.objects.create(
#                 widget=widget,
#                 viewer=viewer,
#                 timestamp=pytz.UTC.localize(datetime.now()),
#             )

#     except Exception:
#         raise Exception
