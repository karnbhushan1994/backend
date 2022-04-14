import json
import logging

from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...common import validator
from ...common.notification_manager import handle_notification
from ...common.validator import check_is_valid_parameter
from ...common.image_manager import profile_pic_url
from ...models import BlockedUser, TaggUser
from ...notifications.models import NotificationType
from .models import (
    Moment,
    MomentTag,
    MomentTagList,
)
from .utils import replace_tags


class MomentTagViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(MomentTagViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        """
            Handles POST request to store tags for a moment
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
            data = request.POST
            user = request.user

            if not check_is_valid_parameter("moment_id", data):
                return Response("moment_id is required", 400)

            if not check_is_valid_parameter("tags", data):
                return Response("tags is required", 400)

            moment_id = data["moment_id"]
            tags = json.loads(data["tags"])

            if not tags:
                return Response("Empty request", 200)

            if not "x" in tags[0]:
                return Response("tag's should only contain x,y,z,user_id", 400)

            if not "y" in tags[0]:
                return Response("tag's should only contain x,y,z,user_id", 400)

            if not "z" in tags[0]:
                return Response("tag's should only contain x,y,z,user_id", 400)

            if not check_is_valid_parameter("user_id", tags[0]):
                return Response("tag's should only contain x,y,z,user_id", 400)

            # Check if moment exists
            if not Moment.objects.filter(moment_id=moment_id).exists():
                return Response("Moment does not exist", 404)

            moment = Moment.objects.get(moment_id=moment_id)

            # Check if request user is allowed to tag users for this moment
            if moment.user_id != user:
                return Response(
                    "User not allowed to tag users for this moment", status=403
                )

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
                    if BlockedUser.objects.filter(
                        blocker=tagg_user, blocked=user
                    ).exists():
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

    def list(self, request):
        """
        Args:
            user_id: Moment id of the moment for which tags have to be created
        Returns:
            Profile picture url for the user tagged in the moment
        """
        try:
            #tma-1856: Returns profile picture URL for the tagged user id
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return Response("user_id is required", 400)
            if TaggUser.objects.filter(id=data["user_id"]).exists():
                user_id = data["user_id"]
                return Response(profile_pic_url(user_id))
            else:
                return Response("user_id is not valid", 500)
        except Exception:
            self.logger.exception("Something went wrong while displaying profile picture")
            return Response("Something went wrong while displaying profile picture", 500)

    def put(self, request, pk=None):
        """
        Handles a PUT request to replace a tag from the moment
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
        return replace_tags(self, request)

    def destroy(self, request, pk):
        """
        Handles a delete request to remove a tag from the moment
        Args:
            pk: id of the moment tag
        Returns:
            Success message with status code
        """
        try:
            # removes moment_tag based on pk
            moment_tag_id = pk
            user = request.user

            # Check if tag exists and if requester is the owner of the tag
            if not MomentTagList.objects.filter(
                moment_tag_id=moment_tag_id, moment_tag__user=user
            ).exists():
                Response("Tag does not exist on user", status=404)

            moment_tag_list_obj = MomentTagList.objects.filter(
                moment_tag_id=moment_tag_id, moment_tag__user=user
            ).first()

            # Check if user is authorized to delete tag
            if (
                user != moment_tag_list_obj.moment_tag.user
                or user != moment_tag_list_obj.moment_id
            ):
                Response("User not authorized to delete tag", status=403)

            # Delete tag
            MomentTag.objects.get(id=moment_tag_list_obj.moment_tag.id).delete()
            moment_tag_list_obj.delete()

            return Response("Success", status=200)

        except AttributeError as err:
            self.logger.exception("Attribute error while removing tag from moment")
            return Response("Attribute error", status=500)

        except Exception as err:
            self.logger.exception("Something went wrong while removing a moment tag")
            return Response("Something went wrong", status=500)