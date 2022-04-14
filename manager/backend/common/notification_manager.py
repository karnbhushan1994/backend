"""
    One stop to create entry in the database for a notification and notify the concerned user via FCM
"""


from ..notifications.models import Notification, NotificationList, NotificationType
from firebase_admin.messaging import Message
# from firebase_admin.messaging import Notification as Firebase_notification
from fcm_django.models import FCMDevice
from ..models import TaggUser

import logging

logger = logging.getLogger(__name__)

notifications_with_titles = {
    NotificationType.FRIEND_REQUEST,
    NotificationType.FRIEND_ACCEPTANCE,
    NotificationType.COMMENT,
    NotificationType.MOMENT_3P,
    NotificationType.MOMENT_FRIEND,
    NotificationType.MOMENT_TAG,
}


class NotifyNotificationException(Exception):
    pass


def handle_bulk_notification(
    notification_type, actor, verbage, notification_object=None
):
    """notify all active users
    Args:
        notification_type: Type of the notification
        actor: Tagg User responsible for the notification, to be excluded from bulk notification
        verbage: Message to be displayed on the notification
        notification_object: Notification object if any
    returns:
        True or false depending on whether the operation passed or failed
    """
    try:
        title = (
            actor.get_full_name()
            if notification_type in notifications_with_titles
            else None
        )

        def get_notification_id():
            if notification_object:
                if notification_type in [
                    NotificationType.MOMENT_3P,
                    NotificationType.MOMENT_FRIEND,
                    NotificationType.MOMENT_TAG,
                ]:
                    return notification_object.moment_id
                else:
                    return None
            return None

        notification = Notification(
            actor=actor,
            verbage=verbage,
            notification_type=notification_type,
            notification_object=get_notification_id(),
            object=notification_object,
        )
        notification.save()

        for userB in TaggUser.objects.all().exclude(username=actor.username):
            notification_list = NotificationList(user=userB, notification=notification)
            notification_list.save()

        notify_all_users(verbage, actor, title)
        return True
    except NotifyNotificationException as e:
        logger.error("Failed to send notification")
    except Exception as err:
        logger.exception("Failed to save / send notification")
    return False


def handle_notification(
    notification_type, actor, receiver, verbage, notification_object=None
):
    """Create notification entry on the database and notify user
    Args:
        notification_type: Type of the notification
        actor: Tagg User responsible for the notification
        receiver: Tagg User receiving the notification
        verbage: Message to be displayed on the notification
        notification_object: Notification object if any
    returns:
        True or false depending on whether the operation passed or failed
    """
    try:
        if (
            notification_type == NotificationType.SYSTEM_MSG
        ):
            # we're relying on Tagg user's profile to display the image in the frontend
            assert actor.username == "Tagg"

        def get_notification_id():
            if notification_object:
                if notification_type == NotificationType.COMMENT:
                    return notification_object.comment_id
                elif notification_type in [
                    NotificationType.MOMENT_3P,
                    NotificationType.MOMENT_FRIEND,
                    NotificationType.MOMENT_TAG,
                ]:
                    return notification_object.moment_id
                else:
                    return None
            return None

        notification = Notification(
            actor=actor,
            verbage=verbage,
            notification_type=notification_type,
            notification_object=get_notification_id(),
            object=notification_object,
        )
        notification.save()
        notification_list = NotificationList(user=receiver, notification=notification)
        notification_list.save()
        if notification_type == NotificationType.CLICK_TAG:
            title = "Tagg Click Count"
        elif notification_type == NotificationType.PROFILE_VIEW:
            title = "Profile Views"
        elif notification_type == NotificationType.MOMENT_VIEW:
            title = "Moment Views"
        else:
            title = (
                actor.get_full_name()
                if notification_type in notifications_with_titles
                else None
            )
        notify_user(receiver, verbage, title)
        return True
    except NotifyNotificationException:
        logger.error("Failed to send notification")
    except Exception as err:
        logger.exception("Failed to save / send notification")
    return False


def handle_notification_with_images(
    notification_type, actor, receiver, title, verbage, image_url, notification_object=None
):
    """Create notification entry on the database with images and notify user
    Args:
        notification_type: Type of the notification
        actor: Tagg User responsible for the notification
        receiver: Tagg User receiving the notification
        verbage: Message to be displayed on the notification
        notification_object: Notification object if any
    returns:
        True or false depending on whether the operation passed or failed
    """
    try:
        if (
            notification_type == NotificationType.SYSTEM_MSG
        ):
            # we're relying on Tagg user's profile to display the image in the frontend
            assert actor.username == "Tagg"

        def get_notification_id():
            if notification_object:
                if notification_type == NotificationType.COMMENT:
                    return notification_object.comment_id
                elif notification_type in [
                    NotificationType.MOMENT_3P,
                    NotificationType.MOMENT_FRIEND,
                    NotificationType.MOMENT_TAG,
                ]:
                    return notification_object.moment_id
                else:
                    return None
            return None

        notification = Notification(
            actor=actor,
            verbage=verbage,
            notification_type=notification_type,
            notification_object=get_notification_id(),
            object=notification_object,
        )
        notification.save()
        notification_list = NotificationList(user=receiver, notification=notification)
        notification_list.save()

        notify_user_with_image(receiver, verbage, title, image_url)
        return True
    except NotifyNotificationException:
        logger.error("Failed to send notification")
    except Exception as err:
        logger.exception("Failed to save / send notification")
    return False


def update_notification(
    user_id, actor_id, current_notification_type, notification_type, verbage
):
    try:
        if NotificationList.objects.filter(user=user_id).exists():
            notifications_list = NotificationList.objects.filter(user=user_id).values(
                "notification_id"
            )
            for notification_list_obj in notifications_list:
                if Notification.objects.filter(
                    id=notification_list_obj["notification_id"],
                    notification_type=current_notification_type,
                    actor_id=actor_id,
                ).exists():
                    notification = Notification.objects.filter(
                        id=notification_list_obj["notification_id"],
                        notification_type=current_notification_type,
                        actor_id=actor_id,
                    )
                    notification.update(
                        notification_type=notification_type, verbage=verbage
                    )
            return True
        else:
            return False
    except Exception as err:
        logging.exception("Error while updating relationship")


def get_all_notification_types():
    return [
        NotificationType.DEFAULT,
        NotificationType.FRIEND_REQUEST,
        NotificationType.FRIEND_ACCEPTANCE,
        NotificationType.COMMENT,
        NotificationType.LINK_TAGGS,
        NotificationType.MOMENT_3P,
        NotificationType.MOMENT_FRIEND,
        NotificationType.INVITEE_ONBOARDED,
        NotificationType.MOMENT_TAG,
        NotificationType.SYSTEM_MSG,
        NotificationType.PROFILE_VIEW,
    ]


def delete_notification(user_id, actor_id, notification_types=[]):
    try:
        if NotificationList.objects.filter(user=user_id).exists():
            notifications_list = NotificationList.objects.filter(user=user_id).values(
                "notification_id"
            )

            if len(notification_types) == 0:
                notification_types = get_all_notification_types()

            for notification_list_obj in notifications_list:
                if Notification.objects.filter(
                    id=notification_list_obj["notification_id"],
                    notification_type__in=notification_types,
                    actor_id=actor_id,
                ).exists():
                    notification = Notification.objects.filter(
                        id=notification_list_obj["notification_id"],
                        notification_type__in=notification_types,
                        actor_id=actor_id,
                    )
                    notification.delete()
                    # delete corresponding notification list item
            return True
        else:
            return False
    except Exception as err:
        logging.exception("Error while updating relationship")


def notify_all_users(verbage, excludeReceiver=None, title=None):
    try:
        FCMDevice.objects.filter(active=1).exclude(user=excludeReceiver).send_message(title=title, body=verbage)
    except Exception as err:
        logger.error(err)
        raise NotifyNotificationException


def notify_user(receiver, verbage, title=None):
    try:
        device = FCMDevice.objects.filter(user=receiver, active=1)[0]
        last_seen = receiver.taggusermeta.last_seen_notifications
        unread_count = NotificationList.objects.filter(
            user=receiver, notification__timestamp__gt=last_seen
        ).count()
        device.send_message(title=title, body=verbage, badge=unread_count)
    except Exception as err:
        raise NotifyNotificationException


def notify_user_with_image(receiver, verbage, title=None, image_url=None):
    try:
        device = FCMDevice.objects.filter(user=receiver, active=1)[0]
        device.send_message(title=title, body=verbage)

        # device.send_message(
        #     Message(
        #         notification=Firebase_notification(
        #             title=title, body=verbage, image=image_url
        #         )
        #     )
        # )
    except Exception as err:
        raise NotifyNotificationException