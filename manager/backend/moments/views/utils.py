from datetime import datetime, timedelta
import logging
import random

import pytz

from ...moments.models import MomentScoreWeights, Moment
from ..utils import increase_moment_score
from .models import MomentViews
from ...common.notification_manager import (
    NotificationType,
    handle_notification_with_images,
)
from ...common.image_manager import profile_pic_url
from ...gamification.constants import TAGG_SCORE_ALLOTMENT
from ...gamification.utils import TaggScoreUpdateException, increase_tagg_score


def record_moment_view_no_notif(moment, viewer):
    """
    To record a view for the given moment by a given user - no notifs sent; this is used for auto processes like boosts, that must not add notifs
    """
    try:
        if moment.user_id != viewer:
            count = random.randint(1, 10)
            for i in range(count):
                MomentViews.objects.create(
                    moment_viewed=moment,
                    moment_viewer=viewer,
                    timestamp=pytz.UTC.localize(datetime.now()),
                )

    except TaggScoreUpdateException as err:
        self.logger.exception("Tagg score update exception")
        return validator.get_response(data="Tagg score update exception", type=500)
    except Exception as err:
        logging.error("There was a problem while recording a moment view ", err)
        raise Exception


def record_moment_view(moment, viewer):
    """
    To record a view for the given moment by a given user
    """
    try:

        if moment.user_id != viewer:
            count = random.randint(1, 10)
            for i in range(count):
                MomentViews.objects.create(
                    moment_viewed=moment,
                    moment_viewer=viewer,
                    timestamp=pytz.UTC.localize(datetime.now()),
                )

                moment_view_count = MomentViews.objects.filter(
                    moment_viewed=moment
                ).count()
                if moment_view_count % 50 == 0:

                    # Update moment score table increase moment score by 10 for every 50 views on a moment
                    # increase_moment_score(moment, count * MomentScoreWeights.VIEW.value) ---> Old functionality: Patched below
                    increase_moment_score(moment, MomentScoreWeights.MOMENTVIEW.value)

                    # send notification for every 50 views
                    handle_notification_with_images(
                        NotificationType.MOMENT_VIEW,
                        moment.user_id,
                        moment.user_id,
                        "Moment Views",
                        f"Congrats, the moment you posted has {moment_view_count}+ views!! Here’s some Tagg coin!",
                        profile_pic_url(moment.user_id),
                        moment,
                    )
                # tma-1888 allow user to earn 10 points per 50 views on total moment views
                total_views = MomentViews.objects.filter(
                    moment_viewed__user_id=moment.user_id,
                ).count()
                # calculate the total views and if it is multiple of 50 tha user will get 10 points rewarded
                if total_views % 50 == 0:
                    increase_tagg_score(
                        moment.user_id, TAGG_SCORE_ALLOTMENT["MOMENT_VIEW"]
                    )

    except TaggScoreUpdateException as err:
        self.logger.exception("Tagg score update exception")
        return validator.get_response(data="Tagg score update exception", type=500)
    except Exception as err:
        logging.error("There was a problem while recording a moment view ", err)
        raise Exception
