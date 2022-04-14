import logging
from datetime import datetime

import pytz
from django.db.models import Q

from ...moments.comments.models import CommentThreads, MomentComments
from ...moments.models import MomentScores
from ...moments.serializers import MomentSerializer
from ...moments.shares.models import MomentShares
from ...moments.views.models import MomentViews
from ..utils import get_start_day_for_applied_filter


def get_total_moment_view_count_by_filter(user, filter_type):
    """
    To retrieve total views a given user's moments have received
    according to the applied filter
    """
    try:
        lowerbound = get_start_day_for_applied_filter(filter_type)
        views = MomentViews.objects.filter(
            moment_viewed__user_id=user,
            timestamp__gte=lowerbound,
            timestamp__lte=pytz.UTC.localize(datetime.now()),
        ).count()

        return views
    except Exception as err:
        logging.exception(
            "There was a problem while retrieving the total moment views for filter ",
            err,
        )
        raise Exception


def get_top_moment_by_filter(user, filter_type):
    """
    To retrieve top moment across user's moments and the said moments comments, shares, views count
    for a given user according to the applied filter
    """
    try:
        now = pytz.UTC.localize(datetime.now())
        lowerbound = get_start_day_for_applied_filter(filter_type)

        top_moment = None
        top_moment_views = 0
        top_moment_shares = 0
        top_moment_comments = 0

        if MomentScores.objects.filter(
            moment__user_id=user,
            timestamp__gte=lowerbound,
            timestamp__lte=now,
        ).exists():
            top_moment_score_card = MomentScores.objects.filter(
                moment__user_id=user,
                timestamp__gte=lowerbound,
                timestamp__lte=now,
            ).order_by("-score")[0]

            top_moment = top_moment_score_card.moment
            top_moment_views = MomentViews.objects.filter(
                moment_viewed=top_moment,
                timestamp__gte=lowerbound,
                timestamp__lte=now,
            ).count()

            top_moment_shares = MomentShares.objects.filter(
                moment_shared=top_moment,
                timestamp__gte=lowerbound,
                timestamp__lte=now,
            ).count()
            top_moment_comments = get_moment_comments_count_by_filter(
                lowerbound, top_moment, top_moment.user_id
            )

        return {
            "moment": MomentSerializer(top_moment, many=False).data
            if top_moment is not None
            else None,
            "views": top_moment_views,
            "shares": top_moment_shares,
            "comments": top_moment_comments,
        }

    except Exception as err:
        logging.exception(
            "There was a problem while retrieving the top moment details for filter ",
            err,
        )
        raise Exception


def get_moment_comments_count_by_filter(lowerbound, moment_id, request_user=None):
    def sum_thread(parent_comment):
        if request_user:
            return CommentThreads.objects.filter(
                Q(parent_comment=parent_comment),
                ~Q(commenter__blocker__blocked=request_user),
                ~Q(commenter__blocked__blocker=request_user),
                date_created__lte=pytz.UTC.localize(datetime.now()),
                date_created__gte=lowerbound,
            ).count()
        else:
            return CommentThreads.objects.filter(
                Q(parent_comment=parent_comment),
                date_created__lte=pytz.UTC.localize(datetime.now()),
                date_created__gte=lowerbound,
            ).count()

    # User should not be able to view comments of the user they are blocked by
    if request_user:
        parent_comments = MomentComments.objects.filter(
            Q(moment_id=moment_id),
            ~Q(commenter__blocker__blocked=request_user),
            ~Q(commenter__blocked__blocker=request_user),
            date_created__lte=pytz.UTC.localize(datetime.now()),
            date_created__gte=lowerbound,
        )
    else:
        parent_comments = MomentComments.objects.filter(
            Q(moment_id=moment_id),
            date_created__lte=pytz.UTC.localize(datetime.now()),
            date_created__gte=lowerbound,
        )

    return (
        sum([sum_thread(parent_comment) for parent_comment in parent_comments])
        + parent_comments.count()
    )
