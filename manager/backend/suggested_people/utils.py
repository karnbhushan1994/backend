import logging
import random

from background_task import background
from django.conf import settings
from django.db.models import Q

from ..common.constants import (
    SpRecommenderFeatureThresholds,
    SpRecommenderFeatureWeights,
)
from ..common.utils import light_shuffle
from ..friends.models import Friends, FriendshipStatusType
from ..friends.utils import find_user_friends
from ..models import SuggestedPeopleLinked
from ..serializers import TaggUser
from .models import PeopleRecommender, UserBadge, Badge


def get_image_and_file_name(user_id):
    """
    Takes in user_id to return image and file name
    Example:
        user_id : 123
        :return image_name : spp-123.png, filename: S3_FOLDER_NAME/image_name
    """
    image_name = f"sdp-{user_id}.png"
    filename = f"{settings.S3_SUGGESTED_PEOPLE_FOLDER}/{image_name}"
    return image_name, filename


def get_badges_for_user(user):
    """
    Takes in a user(TaggUser) and retrieves a list of Badges objects for the user
    """
    user_badge_ids = UserBadge.objects.filter(user=user).values("badge")
    badges = Badge.objects.filter(id__in=user_badge_ids)
    return badges


def get_mutual_badges(user1, user2):
    b1 = get_badges_for_user(user1)
    b2 = get_badges_for_user(user2)
    return list(set(b1).intersection(set(b2)))


def get_mutual_friends(user1, user2, shuffled=False):
    """
    Takes in two users (TaggUser) and retrieves a an intersection of friends list for the user
    """
    friends1 = find_user_friends(user1)
    friends2 = find_user_friends(user2)
    mutual_friends = [
        friend
        for friend in friends1
        if _contains(friends2, lambda object: object.id == friend.id)
    ]
    if shuffled:
        random.shuffle(mutual_friends)
    return mutual_friends


@background(schedule=0)
def mark_user_dirty(user_id):
    user = TaggUser.objects.get(id=user_id)
    prs = PeopleRecommender.objects.filter(Q(recipient=user) | Q(recommendation=user))
    for pr in prs:
        if pr.dirty:
            continue
        pr.dirty = True
        pr.save()


@background(schedule=0)
def mark_users_uninterested_1_count(user_id, uninterested_user_ids):
    user = TaggUser.objects.get(id=user_id)
    uninterested_users = TaggUser.objects.filter(Q(id__in=uninterested_user_ids))
    prs = PeopleRecommender.objects.filter(
        Q(recipient=user), Q(recommendation__in=uninterested_users)
    )
    for pr in prs:
        pr.interested_feature = pr.interested_feature * 0.9
        pr.save()


def _calculate_normalized_feature_value_sum(pr):
    return sum(
        [
            pr.friend_feature * SpRecommenderFeatureWeights.FRIEND,
            pr.university_feature * SpRecommenderFeatureWeights.UNIVERSITY,
            pr.badge_feature * SpRecommenderFeatureWeights.BADGE,
            pr.class_year_feature * SpRecommenderFeatureWeights.CLASS_YEAR,
            pr.interested_feature * SpRecommenderFeatureWeights.INTERESTED,
        ]
    )


def get_suggested_people(user, seed):
    friends = find_user_friends(user)
    # Retrieve IDs of users to whom still-active friend requests were sent.
    requested_users = Friends.objects.filter(
        status=FriendshipStatusType.REQUESTED, requester=user.id
    ).values("requested")
    # Retrieve IDs of users who have sent still-active friend requests.
    requesting_users = Friends.objects.filter(
        status=FriendshipStatusType.REQUESTED, requested=user
    ).values("requester")

    prs = PeopleRecommender.objects.filter(
        Q(recipient=user),
        # filter out friends
        ~Q(recommendation__in=friends),
        # filter out diff universities
        Q(recommendation__university=user.university),
        # filter our users with whom active friend requests exist
        ~Q(recommendation__in=requested_users),
        ~Q(recommendation__in=requesting_users),
        # Filter out users who have blocked the querying user.
        ~Q(recommendation__blocked__blocker=user.id),
    )
    recommendations = sorted(
        prs, key=lambda x: _calculate_normalized_feature_value_sum(x), reverse=True
    )
    recommendations = light_shuffle(
        [r.recommendation for r in recommendations], seed=seed
    )

    """
        Our recommendation system gets updated every 6 hours (as of 2021/05/24).
        A new user does not have the populated PeopleRecommender rows, thus we
        have to use the "dumb" recommender for these new users, for now.
    """
    if not recommendations:
        recommendations = get_suggested_people_dumb(user, seed)

    return recommendations


def get_suggested_people_dumb(user, seed):
    """
    **LEGACY**
    Return suggested people for `user` in an order randomized by `seed`.
    Args:
        user: The user whom to return suggested people for.
        seed: The seed used to randomly shuffle the results, provided by user.
    Returns:
        A list of `user`'s suggested people, shuffled.
    """

    # Retrieve IDs of users to whom still-active friend requests were sent.
    requested_users = Friends.objects.filter(
        status=FriendshipStatusType.REQUESTED, requester=user.id
    ).values("requested")
    # Retrieve IDs of users who have sent still-active friend requests.
    requesting_users = Friends.objects.filter(
        status=FriendshipStatusType.REQUESTED, requested=user
    ).values("requester")

    # Retrieve IDs of users from whom friend requests were accepted.
    friends_requesters = Friends.objects.filter(
        status=FriendshipStatusType.FRIENDS, requested=user.id
    ).values("requester")
    # Retrieve IDs of users to whom friend requests were accepted.
    friends_requestees = Friends.objects.filter(
        status=FriendshipStatusType.FRIENDS, requester=user.id
    ).values("requested")

    users = TaggUser.objects.filter(
        # Filter for users from the same university.
        Q(university=user.university),
        # Filter out users with whom active friend requests exist.
        ~Q(id__in=requested_users),
        ~Q(id__in=requesting_users),
        # Filter out users with whom friendships exist.
        ~Q(id__in=friends_requesters),
        ~Q(id__in=friends_requestees),
        # Filter out users who have blocked the querying user.
        ~Q(blocked__blocker=user.id),
        # Filter out the querying user.
        ~Q(id=user.id),
    )

    results = list(users)
    # Shuffle the results.
    random.Random(seed).shuffle(results)
    return results


def fetch_suggested_people_url(user):
    """
    Takes in a TaggUser object to return suggested_people url
    https://{bucket_name}.s3.us-east-2.amazonaws.com/thumbnails/moments/{resource_id}-thumbnail.jpg
    """
    _, filename = get_image_and_file_name(user.id)
    return f"https://{settings.S3_BUCKET}.{settings.S3_PRE_OBJECT_URI}/{filename}"


def _contains(list, filter):
    for x in list:
        if filter(x):
            return True
    return False


def _is_valid_suggestion(user, cur_user, friends):
    """
    Args:
        user: User for whom suggested people should be returned
        cur_user: User being investigated
        friends: Friends list of user
    Returns
        True if:
            1: cur_user is not the same as passed in user AND
            2: friends list of the passed in user does not include cur_user
        else False
    """
    return user.id != cur_user.id and not _contains(
        friends, lambda object: object.id == cur_user.id
    )


def get_friendship(user, suggested_user):

    friendship_status = "no_record"
    friendship_requester_id = ""
    if Friends.objects.filter(requested=suggested_user.id, requester=user.id).exists():
        record = Friends.objects.filter(
            requested=suggested_user.pk, requester=user.id
        ).values("status")
        friendship_status = record[0]["status"]
        friendship_requester_id = user.id

    elif Friends.objects.filter(
        requested=user.id, requester=suggested_user.id
    ).exists():
        record = (
            Friends.objects.filter(requested=user.id, requester=suggested_user)
            .values("status")
            .values("status")
        )
        friendship_status = record[0]["status"]
        friendship_requester_id = suggested_user.id

    friendship = {"status": friendship_status, "requester_id": friendship_requester_id}
    return friendship


def _calculate_feature_values(pr, a, b):
    """
    Args:
        pr (PeopleRecommender): the recommender
        a (TaggUser): the recipient user
        b (TaggUser): the recommendation user

    Returns
        pr (PeopleRecommender) with features filled in
    """
    pr.friend_feature = min(
        1, len(get_mutual_friends(a, b)) / SpRecommenderFeatureThresholds.FRIEND
    )
    pr.university_feature = 1 if a.university == b.university else 0
    pr.badge_feature = min(
        1, len(get_mutual_badges(a, b)) / SpRecommenderFeatureThresholds.BADGE
    )
    pr.class_year_feature = 1 if a.university_class == b.university_class else 0
    if pr.interested_feature == 0:
        # PR just got initialized, setting it to a proper default value
        pr.interested_feature = 1
    pr.dirty = False
    pr.save()


def insert_recommender_missing_rows():
    """
    Populates the People Recommender table with correct number of rows.

    Constraint:
    The table should always have n*(n-1) number of rows, given n =
    number of existing TaggUsers that're onboarded (taggusermeta__is_onboarded=True).

    Note:
    This only populate empty rows, does not caculate values for efficiency
    reason.
    """
    logger = logging.getLogger("recommender_features")
    try:
        onboarded_users = TaggUser.objects.filter(
            taggusermeta__is_onboarded=True,
            taggusermeta__suggested_people_linked=SuggestedPeopleLinked.FINAL_TUTORIAL,
        )
        for user in onboarded_users:
            for recommendation in onboarded_users:
                if recommendation == user:
                    continue
                pr, created = PeopleRecommender.objects.get_or_create(
                    recipient=user,
                    recommendation=recommendation,
                    defaults={
                        "friend_feature": 0,
                        "university_feature": 0,
                        "badge_feature": 0,
                        "class_year_feature": 0,
                        "interested_feature": 0,
                    },
                )
                if created:
                    logger.info(
                        f"Created row (and marked dirty) for: {user.username} -> {recommendation.username}"
                    )
                    pr.dirty = True
                    pr.save()
                else:
                    logger.debug(
                        f"Skipping: {user.username} -> {recommendation.username}"
                    )
        logger.info("Done")
    except Exception as err:
        logger.error(err)
        logger.error("Something went wrong!")


def compute_recommender_feature_values():
    """
    Populates the People Recommender table with recipient-recommendation feature
    values used for recommendation.
    """
    logger = logging.getLogger("recommender_features")
    try:
        for pr in PeopleRecommender.objects.all():
            if not pr.dirty:
                continue
            logger.info(
                f"Found dirty PR, updating feature values: {pr.recommendation.username} -> {pr.recipient.username}"
            )
            _calculate_feature_values(pr, pr.recipient, pr.recommendation)
        logger.info("Done")
    except Exception as err:
        logger.error(err)
        logger.error("Something went wrong!")
