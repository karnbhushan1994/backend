import decimal
import logging
import re
from datetime import datetime
from telnetlib import STATUS

import pytz
from django.db.models import Q
import random
from backend.models import TaggUserMeta,TaggUser

from ..common.constants import NUM_MOMENT_RECOMMENDATAIONS
from ..common.image_manager import moment_thumbnail_url
from ..common.tagg_data_science import calculate_engagement_value
from .models import Moment, MomentEngagement, MomentScores,DailyMoment

logger = logging.getLogger(__name__)


def get_pre_path(user_id, moment):
    """Returns s3 moments pre_path

    Args:
        user_id : (int) id of the user
        moment : (str) moment_category of the images to be uploaded / retrieved

    Returns:
        (str) path up until the moments folder
    """
    return f"{user_id}/{moment}/" if moment else f"{user_id}/"


def get_pre_s3_uri(bucket, pre_s3):
    """Returns s3 moments pre_uri

    Args:
        bucket : (str) bucket_name of the user
        pre_s3 : (str) moment_category of the images to be uploaded / retrieved

    Returns:
        (str) path excluding the moments folder and image name
    """
    return f"https://{bucket}.{pre_s3}/"


def get_thumbnail_url(moment_url):
    m = re.match(r".*moments\/(.*?)\.(.*)", moment_url)
    if m:
        resource_id = m[1]
        return moment_thumbnail_url(resource_id)
    else:
        return moment_url


def get_user_moments(user, category):
    """
    Retrieve all moments if category is not specified, else retrieve moments
    specific to that category
    """
    if category:
        return Moment.objects.filter(user_id=user, moment_category=category).order_by(
            "-date_created"
        )
    else:
        return Moment.objects.filter(user_id=user).order_by("-date_created")


def suggest_moments_naive(user):
    # recent_moments = Moment.objects.filter(~Q(user_id=user)).order_by("-date_created")[
    #     :50
    # ]
    # random.shuffle(list(recent_moments))
    recent_moments = Moment.objects.filter(
        ~Q(user_id__blocked__blocker=user.id),
        ~Q(user_id__blocker__blocked=user.id),
    ).order_by("-date_created")
    return recent_moments[:NUM_MOMENT_RECOMMENDATAIONS]


def keep_only_top_x_engaged_moment_posts(user, x):
    sorted_mes = sorted(
        MomentEngagement.objects.filter(user=user),
        key=lambda me: calculate_engagement_value(me),
    )
    for me in sorted_mes[:-x]:
        me.delete()


def increase_moment_score(moment, score):
    """
    To record a view for the given moment by a given user
    """
    try:
        lowerbound = pytz.UTC.localize(datetime.now()).replace(
            hour=0, minute=0, second=0
        )
        upperbound = pytz.UTC.localize(datetime.now()).replace(
            hour=23, minute=59, second=59
        )
        if MomentScores.objects.filter(
            moment=moment, timestamp__lte=upperbound, timestamp__gte=lowerbound
        ).exists():
            score_card = MomentScores.objects.filter(
                moment=moment, timestamp__lte=upperbound, timestamp__gte=lowerbound
            )[0]
            score_card.score = score_card.score + decimal.Decimal(score)
            score_card.save()
        else:
            MomentScores.objects.create(
                moment=moment,
                score=score,
            )

    except Exception as err:
        logging.error("There was a problem while recording a moment view ", err)
        raise Exception

def dailyMoments():
        today=datetime.now().date()
        users= TaggUserMeta.objects.filter(is_onboarded=True)
        for user in users:
            if user.user_id:
                taggUser=TaggUser.objects.filter(id=user.user_id).first()
                if taggUser:
                    dailyObj=DailyMoment.objects.filter(date=today,user=taggUser)
                    if not dailyObj:
                        momentsObj=Moment.objects.filter(~Q(user_id=taggUser))
                        moments = list(momentsObj)
                        random.shuffle(moments)
                        for momentObj in moments:
                            if momentObj.user_id_id:
                                owner=TaggUser.objects.filter(id=momentObj.user_id_id).first()
                                if owner:
                                    ObjCheck=DailyMoment.objects.filter(user=taggUser,moment=momentObj)
                                    objCheck3=DailyMoment.objects.filter(user=taggUser,date=today,owner_id=owner)
                                    ObjCheck2=DailyMoment.objects.filter(user=taggUser,date=today).count()
                                    if ObjCheck2==7:
                                        break
                                    if not ObjCheck and ObjCheck2<7:
                                        if not objCheck3:
                                            DailyMoment.objects.create(date=today,user=taggUser,moment=momentObj,status=False,owner_id=owner)
                                            