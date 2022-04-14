from itertools import chain

from django.db.models import Q

from ..models import TaggUser
from .models import Friends


def get_friendship_status(request_user, pk):
    """Figures out the current friendship status between two users,
    optionally looks for the requester if a friend request is in progress/

    Args:
        request_user (TaggUser): the requester user
        pk (str): the target user
    """
    friendship_status = "no_record"
    friendship_requester_id = ""
    if Friends.objects.filter(requested=pk, requester=request_user.id).exists():
        record = Friends.objects.filter(requested=pk, requester=request_user.id).values(
            "status"
        )
        friendship_status = record[0]["status"]
        friendship_requester_id = request_user.id

    elif Friends.objects.filter(requested=request_user.id, requester=pk).exists():
        record = (
            Friends.objects.filter(requested=request_user.id, requester=pk)
            .values("status")
            .values("status")
        )
        friendship_status = record[0]["status"]
        friendship_requester_id = pk
    return friendship_status, friendship_requester_id


def find_user_friends(user_id):
    """Finds the user's friends.
    Args:
        user_id: the id of the user
    """
    # Remove blocked users from list of the requesting user
    # TODO TMA 540: Remove blocked person from their friends list the momen they are blocked
    # if BlockedUser.objects.filter(blocked__id=user_id).exists():
    #     blocked = BlockedUser.objects.filter(blocked__id=user_id)

    friends = []

    # list of friends who the user received the friend request
    requester_friends = Friends.objects.filter(
        requested=user_id, status="friends"
    ).values("requester")

    # list of friends who the user sent the friend request
    requested_friends = Friends.objects.filter(
        requester=user_id, status="friends"
    ).values("requested")

    # Retriving the corresponding TaggUsers for both the user lists
    friends = set(
        chain(
            TaggUser.objects.filter(Q(requester__requester__in=requester_friends)),
            TaggUser.objects.filter(Q(requested__requested__in=requested_friends)),
        )
    )

    return friends


def get_user_friend_count(user):
    requested_friends_count = Friends.objects.filter(
        requested=user, status="friends"
    ).count()
    requester_friends_count = Friends.objects.filter(
        requester=user, status="friends"
    ).count()
    return requested_friends_count + requester_friends_count
