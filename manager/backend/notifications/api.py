from datetime import datetime, timedelta
import logging
import pytz

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import NotificationList, NotificationType
from .serializers import NotificationListSerializer
from rest_framework.pagination import LimitOffsetPagination


class NotificationListViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = LimitOffsetPagination

    def __init__(self, *args, **kwargs):
        super(NotificationListViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        notifications = NotificationList.objects.filter(user=request.user).order_by(
            "-notification__timestamp"
        )

        paginated_notification_list = self.paginate_queryset(notifications)

        return self.get_paginated_response(
            NotificationListSerializer(paginated_notification_list, many=True).data
        )

    @action(methods=["GET"], detail=False)
    def unread_count(self, request, pk=None):
        """
        To get the count of unread notifications for- Comments, Friend Requests, Profile Views, Tags

        Args:
            None

        Returns:
            {
                NotificationType: Count of unread notifications of this type
            }
        """

        try:
            user = request.user

            # Retrieve user's last seen time for notifications (2021 jan 1st || last seen in the last 7 days (both being true we should get a list of unread notifications))
            retrieved_last_seen = user.taggusermeta.last_seen_notifications
            past_week = pytz.UTC.localize(datetime.now() - timedelta(days=7))

            if retrieved_last_seen > past_week:
                last_seen = retrieved_last_seen
            else:
                last_seen = past_week

            # Retireve user's notifications from notifications list, TODO: Filter unread using last seen time:  and Q(notification__timestamp__gt=last_seen)
            unread_comment_count = NotificationList.objects.filter(
                user=user,
                notification__notification_type=NotificationType.COMMENT,
                notification__timestamp__gt=last_seen,
            ).count()
            unread_friend_count = NotificationList.objects.filter(
                user=user,
                notification__notification_type__in=[
                    NotificationType.FRIEND_ACCEPTANCE,
                    NotificationType.FRIEND_REQUEST,
                ],
                notification__timestamp__gt=last_seen,
            ).count()
            unread_view_count = NotificationList.objects.filter(
                user=user,
                notification__notification_type=NotificationType.PROFILE_VIEW,
                notification__timestamp__gt=last_seen,
            ).count()
            unread_tag_count = NotificationList.objects.filter(
                user=user,
                notification__notification_type=NotificationType.MOMENT_TAG,
                notification__timestamp__gt=last_seen,
            ).count()
            unread_click_count = NotificationList.objects.filter(
                user=user,
                notification__notification_type=NotificationType.CLICK_TAG,
                notification__timestamp__gt=last_seen,
            ).count()
            unread_moment_view_count = NotificationList.objects.filter(
                user=user,
                notification__notification_type=NotificationType.MOMENT_VIEW,
                notification__timestamp__gt=last_seen,
            ).count()

            response = {
                NotificationType.COMMENT: unread_comment_count,
                NotificationType.FRIEND_REQUEST: unread_friend_count,  # Includes FriendAccept
                NotificationType.PROFILE_VIEW: unread_view_count,
                NotificationType.MOMENT_TAG: unread_tag_count,
                NotificationType.CLICK_TAG: unread_click_count,
                NotificationType.MOMENT_VIEW: unread_moment_view_count,
            }

            return Response(response, status=200)

        except Exception as error:
            self.logger.exception(
                "There was a problem trying to fetch unread notification counts ", error
            )
            return Response(
                "There was a problem trying to fetch unread notification counts",
                status=500,
            )

    @action(detail=False, methods=["POST"])
    def seen(self, request):
        """
        Note down when notification screen was opened by the user

        Args: None

        Returns success status of request
        """
        try:
            user = request.user

            user.taggusermeta.last_seen_notifications = datetime.now()
            user.taggusermeta.save()

            return Response("Successfully recorded timestamp", status=204)

        except Exception as error:
            self.logger.exception("Problem recording notification last seen ", error)
            return Response("Problem recording notification last seen", status=500)
