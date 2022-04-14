import json
import logging
import random

import requests
from django.conf import settings
from django.utils import timezone

from ..moments.models import Moment, MomentEngagement
from .constants import NUM_MOMENT_RECOMMENDATAIONS

logger = logging.getLogger(__name__)

ENV_STRINGS = {
    "DEV": "dev",
    "UAT": "uat",
    "PROD": "prod",
}


def mark_moment_as_viewed(user, moment):
    payload = {"moment_id": str(moment.moment_id), "user_id": str(user.id)}
    response = requests.post(
        settings.DS_ML_SERVICE + "viewed_moment/",
        data=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "recsystem-mode": ENV_STRINGS.get(settings.ENV, "prod"),
        },
    )
    # if response.status_code != 200:
        # logger.error("Error sending moment viewed")


def get_moment_recommendataions(user):
    mes = MomentEngagement.objects.filter(user=user)
    payload = {
        "user_id": str(user.id),
        "engaged_moments": [
            str(me.moment.moment_id)
            for me in sorted(mes, key=lambda x: calculate_engagement_value(x))
        ],
        "num_recommendations": NUM_MOMENT_RECOMMENDATAIONS,
    }

    try:
        response = requests.post(
            settings.DS_ML_SERVICE + "recommendation/",
            data=json.dumps(payload),
            headers={
                "Content-Type": "application/json",
                "recsystem-mode": ENV_STRINGS.get(settings.ENV, "prod"),
            },
        )
        if response.status_code == 200:
            recommendations = response.json().get("recommendations", [])

            if not recommendations:
                logger.error(
                    "Error fetching moment recommendations: Got back empty moments"
                )
                return []
            moments = Moment.objects.filter(moment_id__in=recommendations)

            if not moments:
                logger.error(
                    "Error fetching moment recommendations: Unable to find any matching moments"
                )
                return []

            return moments
        else:
            logger.error("Error fetching moment recommendations")
            return []
    except Exception as err:
        logger.error(err)
        return []


def calculate_engagement_value(me):
    """
    Business logic for calculating an "Engagement Value" for each
    moment view based on a couple attributes.
    """
    score = 0
    score += me.view_duration
    if me.creation_date:
        score -= (timezone.now() - me.creation_date).days
    score += me.clicked_on_profile * 10
    score += me.clicked_on_comments * 10
    score += me.clicked_on_share * 10
    return score
