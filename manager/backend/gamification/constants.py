import enum


GAMIFICATION_TIER_DATA = {
    1: {
        "title": "New kid on the Block",
        "min_score": 0,
    },
    2: {
        "title": "Apprentice",
        "min_score": 50,
    },
    3: {
        "title": "Artisan",
        "min_score": 100,
    },
    4: {
        "title": "Specialist",
        "min_score": 150,
    },
    5: {
        "title": "Socialite",
        "min_score": 200,
    },
}


class GamificationTier(enum.Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


"""
    Tagg Score awarded per action

        + Post a Moment: 5 XP

        + Comment on Moment: 1 XP

        + Share a Moment: 1 XP

        + Edit page color: 5 XP
            - User must change the current selected page (background/tab) color and save it to the profile

        + Add a tagg: 5 XP

        + Edit a tagg: 5 XP
            - User most change the current selected tagg color and save it to the profile

        + Create a page: 10 XP

        + Share a Profile: 10 XP
            - Pressing the share profile button

        + Total moment views: 10 XP
            - Awarded per 50 total views
"""
TAGG_SCORE_ALLOTMENT = {
    "MOMENT_POST": 5,
    "FIRST_MOMENT_POSTED": 50,
    "MOMENT_CREATE": 2,
    "MOMENT_COMMENT": 1,
    "MOMENT_SHARE": 4,
    "TAGG_CREATE": 5,
    "TAGG_EDIT": 2,
    "TAGG_EDIT_COLOR": 2,
    "TAGG_CLICK_COUNT_10": 5,
    "PAGE_CREATE": 1,
    "PROFILE_EDIT_COLOR": 5,
    "PROFILE_SHARE": 5,
    "MOMENT_VIEW": 10,
    "PROFILE_CLICK_COUNT_5": 5,
}

# Coversion rate to convert tagg coins to USD
TAGG_SCORE_TO_USD_RATE = 0.20 # USD/tagg_coin
