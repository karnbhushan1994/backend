APP_STORE_LINK = (
    "https://apps.apple.com/us/app/tagg-discover-your-community/id1537853613"
)

BIO_MAX_LENGTH = 150
GENDER_MAX_LENGTH = 20
UNIVERSITY_MAX_LENGTH = 256

HOMEPAGE = "__TaggUserHomePage__"


class SpRecommenderFeatureWeights:
    FRIEND = 0.5
    UNIVERSITY = 0.05
    BADGE = 0.2
    CLASS_YEAR = 0.05
    INTERESTED = 0.2


class SpRecommenderFeatureThresholds:
    """
    Consider any feature's mutual count above X to be the same as X.
    E.g. We consider 50 mutual friends is the same as 51, 60, or 1000 mutual
    friends.
    """

    FRIEND = 50
    BADGE = 5


"""
    This is the limit for how many contacts a Tagg user can invite in our 
    Invite Friends feature.
"""
INVITE_FRIEND_LIMIT = 7

"""
    (2021/05/13) We decided that we want to reset everyone's invitation count
    back to 7. So we initialized all InviteFriend objects to assume that it was
    created on 5/1. So we can then only count invites that were made after 5/1
    to count towards the invite limit.
"""
INVITE_FRIEND_RESET_DATE = "2021-05-01"


# Tagg Data Science
NUM_MOMENT_RECOMMENDATAIONS = 100
NUM_ENGAGED_MOMENTS = 15

# SMS
SMS_WAITLIST_CONFIRMED = """
Wassup? This is Tagg again! As you know, we support our creators as they grow their brand and reward them for creating! But in order to get these REWARDS✨ we need to chat with you directly. Tap the link to our personal cell and text “creator” to register for access to rewards!!

https://my.community.com/tagg
"""

SMS_WAITLIST_APPROVED = """
Hey Creative, your access to Tagg has been verified 🤩 Click the link below to continue!

https://redirect.tagg.id/join
"""
