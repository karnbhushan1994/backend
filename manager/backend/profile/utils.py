import logging

from ..analytics.profile.models import ProfileViews
from ..analytics.profile.utils import get_profile_view_distribution_by_day

from ..common.notification_manager import handle_notification
from ..friends.utils import get_friendship_status
from ..models import TaggUser
from ..notifications.models import NotificationType
from ..social_linking.models import SocialLink
from .serializers import OwnerProfileInfoSerializer, ProfileInfoSerializer

from backend.gamification.utils import get_converted_coins

logger = logging.getLogger(__name__)


def allow_to_view_private_content(request_user, user):
    """
    Helper function to determine if a requester is able to view a user's
    private content or not.

    2021/10/01: Private account is removed.
    """
    return True


def get_profile_info_serialized(requester, pk):
    user = TaggUser.objects.get(id=pk)
    social_link, _ = SocialLink.objects.get_or_create(user_id=user)
    friendship_status, friendship_requester_id = get_friendship_status(requester, pk)
    owner_requesting = str(requester.id) == pk
    serializer = (
        OwnerProfileInfoSerializer if owner_requesting else ProfileInfoSerializer
    )
    serialized = serializer(
        user,
        context={
            "requester_id": str(requester.id),
            "owner_requesting": str(requester.id) == pk,
            "social_link": social_link,
            "friendship_status": friendship_status,
            "friendship_requester_id": friendship_requester_id,
        },
    )
    result = serialized.data
    if requester == user:
        # send conversion from tagg coin to USD if requester
        # is looking at his/her own profile
        result['coin_to_usd'] = get_converted_coins(result['tagg_score'])
    return result


def send_notification_profile_visits():
    """
    Empty profile visits table and send notifications for users who have
    3+ profile visits.
    """
    tagg = TaggUser.objects.get(username="Tagg")
    # for pv in ProfileViews.objects.all().distinct("profile_visited"):
    #     try:
    #         views_by_day = get_profile_view_distribution_by_day(pv.profile_visited, 0)
    #         visits = views_by_day
    #         if visits > 3:
    #             success = handle_notification(
    #                 NotificationType.PROFILE_VIEW,
    #                 actor=tagg,
    #                 receiver=pv.profile_visited,
    #                 verbage="3+ People have viewed your profile!",
    #             )
    #             if success:
    #                 logger.info(
    #                     f"{pv.profile_visited.username} with {visits} visits, notification was sent."
    #                 )
    #             else:
    #                 logger.info(
    #                     f"{pv.profile_visited.username} with {visits} visits, FAILED to send a notification."
    #                 )
    #         pv.delete()
    #     except Exception as err:
    #         logger.error(err)
    #         logger.error("Failed to process", pv.profile_visited.username)
    #         continue
