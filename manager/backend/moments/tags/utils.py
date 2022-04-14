import json
import logging

from rest_framework.response import Response

from ...common import image_manager
from ...common.notification_manager import handle_notification
from ...common.validator import check_is_valid_parameter
from ...models import BlockedUser, TaggUser
from ...moments.models import Moment
from ...notifications.models import NotificationType
from .models import MomentTag, MomentTagList

logger = logging.getLogger(__name__)


def replace_tags(self, request):
    """
    Functionality for a PUT request to replace a tag from the moment

    Args:
        moment_id (form data key): Moment id of the moment for which tags have to be created
        tags (form data key): Array of tag objects [{Tag object}, {}, ...]
                                + Tag objects {"x": "", "y": "", "z": "","user_id": ""}
                                    - x: x coordinate
                                    - y: y coordinate
                                    - z: z coordinate
                                    - user_id: user id of the user that must be tagged

    Returns:
        Success message with status code
    """
    try:
        # Basic algorithm: delete all existing tags for moment, then add new ones
        data = request.data
        user = request.user

        if not check_is_valid_parameter("moment_id", data):
            return Response("moment_id is required", 400)

        if not check_is_valid_parameter("tags", data):
            return Response("tags is required", 400)

        moment_id = data["moment_id"]
        tags = json.loads(data["tags"])

        if not tags:
            return Response("Empty request", 200)

        if (
                not "x" in tags[0]
                or not "y" in tags[0]
                or not "z" in tags[0]
                or not check_is_valid_parameter("user_id", tags[0])
        ):
            return Response("tag's should only contain x,y,z,user_id", 400)

        # Check if moment exists
        if not Moment.objects.filter(moment_id=moment_id).exists():
            return Response("Moment does not exist", 404)

        moment = Moment.objects.get(moment_id=moment_id)

        # Check if request user is allowed to tag users for this moment
        if moment.user_id != user:
            return Response("User not allowed to tag users for this moment", status=403)

        # Part 1: delete old tags

        old_tags = MomentTagList.objects.filter(moment_id=moment_id, moment_tag__user=user)

        if old_tags:
            old_tag = old_tags[0]
            MomentTag.objects.get(id=old_tag.moment_tag.id).delete()
            old_tag.delete()
            # for old_tag_list_obj in old_tags:
            #     # Check if user is authorized to delete tag
            #     if (
            #         user != old_tag_list_obj.moment_tag.user
            #         or user != old_tag_list_obj.moment_id
            #     ):
            #         Response("User not authorized to delete tag", status=403)
            #
            #     # Delete tag
            #     MomentTag.objects.get(id=old_tag_list_obj.moment_tag.id).delete()
            #     old_tag_list_obj.delete()

        for tag in tags:
            if MomentTagList.objects.filter(
                    moment_id=moment_id, moment_tag__user__id=tag["user_id"]
            ).exists():
                moment_tag_list_object = MomentTagList.objects.get(
                    moment_id=moment_id, moment_tag__user__id=tag["user_id"]
                )

                # retrieve moment_tag
                moment_tag = MomentTag.objects.get(
                    id=moment_tag_list_object.moment_tag.id
                )
                moment_tag.x = tag["x"]
                moment_tag.y = tag["y"]
                moment_tag.z = tag["z"]
                moment_tag.save()

            else:
                # Checking if tagg user exists, to tag
                if not TaggUser.objects.filter(id=tag["user_id"]).exists():
                    Response("User does not exist to be tagged", status=403)
                tagg_user = TaggUser.objects.get(id=tag["user_id"])

                # Check if tagg user has blocked the moment owner/tagger
                if BlockedUser.objects.filter(blocker=tagg_user, blocked=user).exists():
                    return Response("Blocked from tagging this user", status=403)

                # Create a new moment tag
                moment_tag = MomentTag.objects.create(
                    x=tag["x"], y=tag["y"], z=tag["z"], user=tagg_user
                )

                # Create new moment_tag list object
                MomentTagList.objects.create(moment_tag=moment_tag, moment=moment)

                # Send notification
                handle_notification(
                    notification_type=NotificationType.MOMENT_TAG,
                    actor=user,
                    receiver=tagg_user,
                    verbage="Tagged you in a moment!",
                    notification_object=moment,
                )

        return Response("Success, users were tagged in the moment", 201)
    except Exception as err:
        self.logger.exception("Something went wrong")
        return Response("Something went wrong", 500)

    except AttributeError as err:
        self.logger.exception("Attribute error while removing tag from moment")
        return Response("Attribute error", status=500)

    except Exception as err:
        self.logger.exception("Something went wrong while removing a moment tag")
        return Response("Something went wrong", status=500)
