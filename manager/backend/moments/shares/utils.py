import logging

from ...moments.models import MomentScoreWeights
from ..utils import increase_moment_score
from .models import MomentShares


def record_moment_share(moment, sharer):
    """
    To record a view for the given moment by a given user
    """
    try:

        share = MomentShares.objects.create(moment_shared=moment, moment_sharer=sharer)

        # Update moment score table
        if share:
            increase_moment_score(moment, MomentScoreWeights.SHARE.value)

        else:
            raise Exception

    except Exception as err:
        logging.error("There was a problem while recording a moment view ", err)
        raise Exception
