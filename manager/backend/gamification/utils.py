from .constants import (
    GAMIFICATION_TIER_DATA, 
    GamificationTier, 
    TAGG_SCORE_TO_USD_RATE
)
from rest_framework.exceptions import APIException
from .constants import GAMIFICATION_TIER_DATA, GamificationTier
from .models import GameProfile


class TaggScoreUpdateException(Exception):
    pass

class TaggScoreNotSufficient(Exception):
    pass

class TaggTierException(APIException):
    status_code = 500
    default_detail = "Unable to update Tier for user"
    default_code = "Unable to update Tier for user"


# Update tagg score and tier
def increase_tagg_score(user, score_earned):
    try:
        game_profile = GameProfile.objects.filter(tagg_user=user).first()
        if game_profile:
            game_profile.tagg_score = game_profile.tagg_score + score_earned
            game_profile.tier = determine_gamification_tier(game_profile.tagg_score)
            game_profile.save()
    except TaggTierException:
        raise TaggTierException
    except:
        raise TaggScoreUpdateException

# Update tagg score and tier
def decrease_tagg_score(user, score_remove):
    try:
        game_profile = GameProfile.objects.filter(tagg_user=user).first()
        if game_profile:
            if game_profile.tagg_score < score_remove:
                raise TaggScoreNotSufficient
            game_profile.tagg_score = game_profile.tagg_score - score_remove
            game_profile.tier = determine_gamification_tier(game_profile.tagg_score)
            game_profile.save()
    except TaggTierException:
        raise TaggTierException
    except:
        raise TaggScoreUpdateException


def has_enough_tagg_score(user, score):
    try:
        game_profile = GameProfile.objects.get(tagg_user=user)
        if game_profile:
            if game_profile.tagg_score < score:
                return False
            return True
    except:
        raise TaggScoreUpdateException


# Returns tagg coins converted to USD upto 2 decimal places
def get_converted_coins(coins: int):
    return round(coins * TAGG_SCORE_TO_USD_RATE, 2)

  
# Determine game tier currently depending on user's current tagg score
def determine_gamification_tier(score):
    # tma-2070 and tma-2031 Update tier for the user based on tagg score
    try:
        if score >= 0 and score <= 2999:
            return GAMIFICATION_TIER_DATA[GamificationTier.ONE.value]["title"]
        elif score <= 5999:
            return GAMIFICATION_TIER_DATA[GamificationTier.TWO.value]["title"]
        elif score <= 8999:
            return GAMIFICATION_TIER_DATA[GamificationTier.THREE.value]["title"]
        elif score <= 11999:
            return GAMIFICATION_TIER_DATA[GamificationTier.FOUR.value]["title"]
        elif score >= 12000:
            return GAMIFICATION_TIER_DATA[GamificationTier.FIVE.value]["title"]
        else:
            raise TaggTierException
    except:
        raise TaggTierException

