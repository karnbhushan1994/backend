import json
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from ..notifications.models import Notification, NotificationType
from ..models import TaggUser, BlockedUser
from ..friends.models import Friends
from ..common.validator import check_is_valid_parameter, get_response
from ..common.notification_manager import delete_notification
from ..common.image_manager import profile_pic_url, profile_thumbnail_url


class BlockUserViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(BlockUserViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        """Block a user (Very similar to the friend / unfriend flow)

        Args:
            blocked (str): Id of the user being blocked

        Returns:
            A status code
        """
        try:
            body = json.loads(request.body)

            error_data = BlockedUser.objects.validate_data(body)
            if len(error_data):
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

            blocker = request.user
            blocked = TaggUser.objects.only("id").get(id=body["blocked"])

            if BlockedUser.objects.filter(blocked=blocked, blocker=blocker).exists():
                return Response(
                    "You have a already blocked the user",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            BlockedUser.objects.create(blocked=blocked, blocker=blocker)

            # Friendship must be ended
            if Friends.objects.filter(requested=blocked, requester=blocker).exists():
                Friends.objects.filter(requested=blocked, requester=blocker).delete()
                delete_notification(
                    user_id=blocked.id,
                    actor_id=blocker.id,
                    notification_types=["FRD_REQ"],
                )
                delete_notification(user_id=blocked.id, actor_id=blocker.id)

            response = {"status": "Success: You have blocked the user"}
            return get_response(data=response, type=201)

        except UnicodeDecodeError:
            self.logger.exception("Expected JSON data in request body.")
            return get_response(data="Expected JSON data in request body.", type=400)
        except json.decoder.JSONDecodeError:
            self.logger.exception("Expected JSON-formatted data.")
            return get_response(data="Expected JSON data in request body.", type=400)
        except TaggUser.DoesNotExist:
            self.logger.exception("Invalid user ID or blocker ID")
            return get_response(data="Invalid user ID or blocker ID", type=400)
        except Exception as err:
            self.logger.exception("A problem occured while adding to the block list")
            return get_response(
                data="A problem occured while adding to the block list", type=500
            )

    def destroy(self, request, pk=None):
        """Unblock a given user

            blocked (str): Id of the user being unblocked

        Returns:
           A status code
        """
        try:
            body = json.loads(request.body)
            error_data = BlockedUser.objects.validate_data(body)
            if len(error_data):
                return Response(error_data, status=status.HTTP_400_BAD_REQUEST)

            blocker = request.user
            blocked = TaggUser.objects.only("id").get(id=body["blocked"])

            if not BlockedUser.objects.filter(
                    blocked=blocked, blocker=blocker
            ).exists():
                return Response(
                    "You have unblocked the user", status=status.HTTP_400_BAD_REQUEST
                )

            BlockedUser.objects.filter(blocked=blocked, blocker=blocker).delete()
            response = {"status": "Success: You have unblocked the user"}
            return Response(response, status=201)
        except UnicodeDecodeError:
            self.logger.exception("Expected JSON data in request body.")
            return get_response(data="Expected JSON data in request body.", type=400)
        except json.decoder.JSONDecodeError:
            self.logger.exception("Expected JSON-formatted data.")
            return get_response(data="Expected JSON data in request body.", type=400)
        except TaggUser.DoesNotExist:
            self.logger.exception("Invalid user ID or blocked ID")
            return get_response(data="Invalid user ID or blocked ID", type=400)
        except Exception as err:
            self.logger.exception("A problem occured while adding to the block list")
            return get_response(
                data="A problem occured while adding to the block list", type=500
            )

    def retrieve(self, request, pk):
        """Checks if the logged in user is blocked by the user he is trying to access

        Args:
            pk (str) : Id of the logged in user
            blocker (str): Id of the user being accessed

        Returns:
            True / False
        """
        try:
            data = request.query_params
            if not check_is_valid_parameter("blocker", data):
                return get_response(data="Missing parameter", type=400)

            user = TaggUser.objects.get(id=pk)

            if request.user.id != user.id:
                self.logger.error("The user id not valid")
                return get_response(data="The user is not valid", type=400)

            is_blocked = BlockedUser.objects.filter(
                blocker=data["blocker"], blocked=user
            ).exists()
            return get_response(data={"is_blocked": is_blocked}, type=200)
        except TaggUser.DoesNotExist:
            self.logger.exception("User does not exist")
            return get_response(data="User does not exist", type=400)
        except BlockedUser.DoesNotExist:
            self.logger.exception("No results found")
            return get_response(data="No results found", type=400)
        except Exception as err:
            self.logger.exception("Problem fetching the blocked list")
            return get_response(data="Problem fetching the blocked list", type=500)

    def list(self, request):
        """List all users blocked by a user
        Args:
            user_id (str) : Id of the user requesting the block list

        Returns:
            A list of blocked users
        """
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return get_response(data="user_id is required", type=400)
            user_id = data.get("user_id")
            blocked_list = TaggUser.objects.filter(blocked__blocker=user_id).values(
                "id", "username", "first_name", "last_name"
            )
            for blist in blocked_list:
                blist.update({
                    "profile_pic": profile_pic_url(blist.get("id")),
                    "profile_thumbnail": profile_thumbnail_url(blist.get("id"))
                })
            return get_response(data=blocked_list, type=200)

        except TaggUser.DoesNotExist:
            self.logger.exception("User does not exist")
            return get_response(data="User does not exist", type=400)
        except BlockedUser.DoesNotExist:
            self.logger.exception("No results found")
            return get_response(data="No results found", type=400)
        except Exception as err:
            self.logger.exception("Problem fetching the blocked list")
            return get_response(data="Problem fetching the blocked list", type=500)
