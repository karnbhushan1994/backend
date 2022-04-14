from datetime import datetime
from ..models import InviteFriends

from django.db.models.query_utils import Q

from ..common.constants import INVITE_FRIEND_LIMIT, INVITE_FRIEND_RESET_DATE


def invites_left(user):
    return (
        INVITE_FRIEND_LIMIT
        - InviteFriends.objects.filter(
            Q(inviter=user),
            Q(created_date__gt=datetime.strptime(INVITE_FRIEND_RESET_DATE, "%Y-%m-%d")),
        ).count()
    )
