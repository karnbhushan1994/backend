from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from ..models import TaggUser
import logging
from ..common.notification_manager import delete_notification

"""
    Manager to validate and create relationship between two people
"""


class FriendshipStatusType(models.TextChoices):
    REQUESTED = "requested"
    FRIENDS = "friends"


class FriendsManager(BaseUserManager):
    def validate_data(self, body):
        """
        requested : user who is being added as a friend
        """
        errors = {}
        if not "requested" in body or len(body["requested"]) == 0:
            errors["requested"] = "requested User's Id is required"

        return errors

    def create_relationship(self, requester, requested, status):

        relationship = self.model(
            requester=requester, requested=requested, status=status
        )

        relationship.save()
        return relationship

    # Updating relationship status to "friends" from "requested"
    def update_relationship(self, requester, requested, status):
        try:
            if Friends.objects.filter(
                requester=requester, requested=requested, status="requested"
            ).exists():
                relationship = Friends.objects.filter(
                    requester=requester, requested=requested, status="requested"
                )
                relationship.update(status=status)
                return True

            else:
                return False

        except Exception as err:
            logging.exception("Error while updating relationship")

    def delete_relationship(self, userB, userA, reason):
        if Friends.objects.filter(requested=userA.id, requester=userB.id).exists():
            Friends.objects.filter(requested=userA.id, requester=userB.id).delete()

            # user A is the actor, delete the notification sent to user = user A, actor = user B
            if reason == "cancelled" or reason == "declined":
                delete_notification(
                    user_id=userA.id, actor_id=userB.id, notification_type="FRD_REQ"
                )
            return True

        elif Friends.objects.filter(requested=userB.id, requester=userA.id).exists():
            Friends.objects.filter(requested=userB.id, requester=userA.id).delete()
            # user B is the actor, delete the notification sent to user = user B, actor = user A
            if reason == "cancelled" or reason == "declined":
                delete_notification(
                    user_id=userB.id, actor_id=userA.id, notification_type="FRD_REQ"
                )
            return True

        else:
            return False


class Friends(models.Model):
    requester = models.ForeignKey(
        TaggUser,
        on_delete=models.CASCADE,
        related_name="requester",
        db_column="requester",
    )
    requested = models.ForeignKey(
        TaggUser,
        on_delete=models.CASCADE,
        related_name="requested",
        db_column="requested",
    )
    status = models.CharField(
        max_length=50,
        choices=FriendshipStatusType.choices,
        default=FriendshipStatusType.REQUESTED,
    )

    objects = FriendsManager()

    class Meta:
        unique_together = ("requester", "requested")
