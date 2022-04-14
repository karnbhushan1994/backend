import logging
import re
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from ..common.notification_manager import (
    NotificationList,
    NotificationType,
    handle_notification,
    handle_bulk_notification,
)
from ..friends.models import Friends, FriendshipStatusType
from ..models import TaggUser
from ..moments.models import Moment
from ..social_linking.models import SocialLink
from ..widget.models import Widget
from ..analytics.widgets.utils import (
    record_widget_click,
)
from ..moments.views.utils import record_moment_view_no_notif


def link_taggs_reminder():
    logger = logging.getLogger("link_taggs_reminder")
    logger.info("Started")
    for user in TaggUser.objects.all():
        try:
            link = None
            try:
                link = SocialLink.objects.get(user_id=user)
            except SocialLink.DoesNotExist:
                pass
            if not link or __number_of_linked_socials(link) < 2:
                diff = (timezone.now() - user.date_joined).days
                if diff in [1, 3, 7, 14, 30]:
                    success = handle_notification(
                        NotificationType.LINK_TAGGS,
                        user,
                        user,
                        "Don't forget to link one of your social tagg!",
                    )
                    if success:
                        msg = f"Send a reminder to {user.username}"
                    else:
                        msg = f"Failed to send a reminder to {user.username}"
                    logger.info(msg)
        except Exception as error:
            logger.exception(error)
            logger.error(
                f"Failed to check user for link taggs reminder: {user.username}"
            )
            continue


def widget_view_boost():
    logger = logging.getLogger("widget_view_boost")
    logger.info("Started widget_view_boost")
    user = TaggUser.objects.all().first()
    for widget in Widget.objects.filter(active=True):
        try:
            record_widget_click(widget, user)
            # msg = f"Recorded widget click for widget: {widget.id}"
            # logger.info(msg)
        except Exception as error:
            logger.exception(error)
            logger.error(f"Failed to record widget for widget: {widget.id}")
            continue
    logger.info("Started moment_view_boost")
    for momentObj in Moment.objects.all():
        try:
            record_moment_view_no_notif(momentObj, user)
        except Exception as error:
            logger.exception(error)
            logger.error(
                f"Failed to record moment view for moment: {momentObj.moment_id}"
            )
            continue


def moments_posted_reminder():
    """
    For every user on tagg, send them a notification if 2 or more users posted a moment in the last 1 hour
    """
    logger = logging.getLogger("moments_posted_reminder")
    logger.info(f"Started : {NotificationType.MOMENT_3P}")
    try:
        message = lambda count: f"And {count} others posted a moment!"
        time_threshold = datetime.now() - timedelta(hours=1)
        relevant_friends = __fetch_relevant_friends(time_threshold)
        if len(relevant_friends) >= 2:
            # Sort and find the user who posted a moment in the most recent past
            relevant_friends = sorted(
                relevant_friends,
                key=lambda object: object[1].date_created,
                reverse=True,
            )
            relevant_friend = relevant_friends[0]

            if handle_bulk_notification(
                NotificationType.MOMENT_3P,
                relevant_friend[0],
                message(len(relevant_friends)),
                relevant_friend[1],
            ):
                logger.info(f"Sent notification for {relevant_friend[0].username}")
            else:
                logger.info(
                    f"Failed sending notification for {relevant_friend[0].username}"
                )
    except Exception as error:
        logger.exception(error)
        logger.info(f"Failed : {NotificationType.MOMENT_3P}")
    logger.info(f"Finished : {NotificationType.MOMENT_3P}")


def __fetch_relevant_friends(time_threshold):
    """
    Find users who posted a moment in the recent past
    """
    # We could get away with using an array, but since we will need this information later, using it anyways
    valid_friends = []

    # Fetch all friends of the user
    friends = TaggUser.objects.all()
    for object in friends:
        friend = object

        # Fetch the latest moment posted by the friend if any
        moment = (
            Moment.objects.filter(Q(date_created__gt=time_threshold), Q(user_id=friend))
            .order_by("-date_created")
            .first()
        )
        if moment:
            valid_friends.append([friend, moment])
    return valid_friends


def moment_posted_friend():
    """
    For every user on tagg, send a notification to all other users if the user posted 1+ moments to the same category in the last 1 hours
    """

    logger = logging.getLogger("moments_posted_reminder")
    logger.info(f"Started : {NotificationType.MOMENT_FRIEND}")
    try:
        message = lambda count, category: f"Posted {count} moments to {category}!"
        check_for_same_category = (
            lambda moment1, moment2: moment1.moment_category == moment2.moment_category
        )
        for user in TaggUser.objects.all():
            time_threshold = datetime.now() - timedelta(hours=1)

            # Fetch the moments posted by user
            moments = Moment.objects.filter(
                Q(date_created__gt=time_threshold), Q(user_id=user)
            ).order_by("-date_created")
            if len(moments) >= 1:
                # Send a notification for the latest moment
                moment = moments[0]

                if handle_bulk_notification(
                    NotificationType.MOMENT_FRIEND,
                    user,
                    message(len(moments), moment.moment_category),
                    moment,
                ):
                    logger.info(f"Sent notification for {user.username}")
                else:
                    logger.info(f"Failed sending notification for {user.username}")
    except Exception as error:
        logger.exception(error)
        logger.info(f"Failed : {NotificationType.MOMENT_FRIEND}")
    logger.info(f"Success : {NotificationType.MOMENT_FRIEND}")


def __number_of_linked_socials(social_link):
    linked = 0
    if social_link.fb_user_id:
        linked += 1
    if social_link.ig_user_id:
        linked += 1
    if social_link.twitter_user_id:
        linked += 1
    if social_link.snapchat_username:
        linked += 1
    if social_link.tiktok_username:
        linked += 1
    return linked


def notify_mentioned_users(
    notification_type,
    mentioned_verbage,
    notification_verbage,
    actor,
    notification_object,
):
    # Extract all user_id's of mentioned users here
    mentions_regex = r"@\[(.+?)\]\((.+?)\)"
    mentioned_users = re.findall(mentions_regex, mentioned_verbage)
    mentioned_users_list = []

    # Mentioned users should all get notifications
    for user_tuple in mentioned_users:
        user = TaggUser.objects.filter(id=user_tuple[1]).first()
        mentioned_users_list.append(user)
        handle_notification(
            notification_type=notification_type,
            actor=actor,
            receiver=user,
            verbage=notification_verbage,
            notification_object=notification_object,
        )

    return mentioned_users_list
