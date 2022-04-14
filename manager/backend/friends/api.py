import json
import logging
from ..suggested_people.utils import mark_user_dirty

from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated

from ..common.notification_manager import (
    NotificationType,
    handle_notification,
    update_notification,
)
from ..common.validator import check_is_valid_parameter, get_response
from ..models import BlockedUser, TaggUser
from ..serializers import FriendsSerializer, TaggUserSerializer
from .models import Friends
from .utils import find_user_friends
from ..profile.utils import allow_to_view_private_content
from rest_framework.response import Response


class FriendsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Friends.objects.all()
    serializer_class = FriendsSerializer

    def __init__(self, *args, **kwargs):
        super(FriendsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        """
        Creates a table entry for friend request

        args (in request body as JSON) :
            requested - user requested for friendship

        returns :
            status of the storage of the received friend request
        """
        try:
            body = json.loads(request.body)
            error_data = Friends.objects.validate_data(body)
            if len(error_data):
                return get_response(error_data, type=400)

            requester = TaggUser.objects.get(id=request.user.id)
            requested = TaggUser.objects.get(id=body["requested"])

            # Do not allow blocked users to send request
            if BlockedUser.objects.filter(
                blocked=requested, blocker=requester
            ).exists():
                return get_response("User has blocked you", type=400)

            # Do not allow blocked users to send request
            if BlockedUser.objects.filter(
                blocked=requester, blocker=requested
            ).exists():
                return get_response("You have blocked this user", type=400)

            if Friends.objects.filter(
                requested=requested, requester=requester, status="friends"
            ).exists():
                return get_response("You are already friends with the user", type=400)
            if Friends.objects.filter(
                requested=requested, requester=requester, status="requested"
            ).exists():
                return get_response("You have already sent a friend request", type=400)

            Friends.objects.create_relationship(
                requested=requested, requester=requester, status="requested"
            )

            # Notifying the requested user of their new friend request
            handle_notification(
                NotificationType.FRIEND_REQUEST,
                requester,
                requested,
                "Sent you a friend request!",
            )

            return get_response("You have sent the friend request!", type=201)

        except UnicodeDecodeError:
            self.logger.exception("Expected JSON data in request body.")
            return get_response("Expected JSON data in request body.", type=400)

        except json.decoder.JSONDecodeError:
            self.logger.exception("Expected JSON-formatted data.")
            return get_response("Expected JSON-formatted data.", type=400)

        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user ID or user's ID")
            return get_response("Invalid user ID or friend's ID", type=400)

        except Exception as err:
            self.logger.exception("Internal server error")
            return get_response("Internal server error", type=500)

    def partial_update(self, request, pk=None):
        """
        Updates the friendship status from "requested" to "friends"

        args (as part of the url):
            pk - user id of the friend request sender

        returns:
            status of the updation of the accepted friend request
        """
        try:
            request_sender = TaggUser.objects.get(id=pk)
            request_accepter = TaggUser.objects.get(id=request.user.id)

            updateStatus = Friends.objects.update_relationship(
                requested=request_accepter, requester=request_sender, status="friends"
            )

            if updateStatus:
                # Notifying the friend request sender of the acceptance
                handle_notification(
                    NotificationType.FRIEND_ACCEPTANCE,
                    request_accepter,
                    request_sender,
                    "@" + request_accepter.username + " is now your friend!",
                )
                # Update notification table containing request to accepted and change notification type to accepted
                update_notification(
                    user_id=request_accepter.id,
                    actor_id=request_sender.id,
                    current_notification_type="FRD_REQ",
                    notification_type="FRD_ACPT",
                    verbage="@" + request_sender.username + " is now your friend!",
                )
                mark_user_dirty(str(request_sender.id))
                mark_user_dirty(str(request_accepter.id))
                return get_response("New friend!", type=201)

            else:
                return get_response("Bad Request", type=400)

        except UnicodeDecodeError:
            self.logger.exception("Expected JSON data in request body.")
            return get_response("Expected JSON data in request body.", type=400)

        except json.decoder.JSONDecodeError:
            self.logger.exception("Expected JSON-formatted data.")
            return get_response("Expected JSON-formatted data.", type=400)

        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user ID or user's ID")
            return get_response("Invalid user ID or friend's ID", type=400)

        except Friends.DoesNotExist:
            self.logger.error("Invalid user ID or friend ID")
            return get_response("Request was never sent to be accepted", type=400)

        except Exception as err:
            self.logger.exception("Internal server error")
            return get_response("Internal server error", type=500)

    def destroy(self, request, pk=None):
        """
        Deletes the record of friendship of the two users

        args:
            pk - user id of the user unfriending another
            reason - Request Cancellation / Declined Request

        returns :
            status of the deletion of the record
        """
        try:
            userA = TaggUser.objects.get(id=request.user.id)
            userB = TaggUser.objects.get(id=pk)

            body = json.loads(request.body)
            reason = body["reason"]

            # Finding the record to be deleted by determining the role of
            # the user when friend request was first sent - requester/requested user
            # Deleting the record if found
            delete_status = Friends.objects.delete_relationship(
                userB, userA, reason=reason
            )

            if delete_status:
                mark_user_dirty(str(userA.id))
                mark_user_dirty(str(userB.id))
                return get_response("You have unfriended the user", type=200)

            else:
                self.logger.error("Invalid user ID or user's ID")
                return get_response("Invalid user ID or user's ID", type=400)

        except UnicodeDecodeError:
            self.logger.exception("Expected JSON data in request body.")
            return get_response("Expected JSON data in request body.", type=400)

        except json.decoder.JSONDecodeError:
            self.logger.exception("Expected JSON-formatted data.")
            return get_response("Expected JSON-formatted data.", type=400)

        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user ID or user's ID")
            return get_response(
                "Invalid user ID or user's ID: A - " + userA.id + " & B - " + userB.id,
                type=400,
            )

        except Friends.DoesNotExist:
            self.logger.error("Invalid user ID or friend ID")
            return get_response(
                "Invalid user ID or friend ID: B - " + userB.id + " & A - " + userA.id,
                type=400,
            )

        except Exception as err:
            self.logger.exception("Internal server error")
            return get_response("Internal server error", type=500)

    def list(self, request):
        """
        Returns the list of friends for a user

        args (as part of query params) :
            user_id - user id of the user whose friends list
                 has been requested for
        """
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return get_response(data="user_id is required", type=400)

            user = TaggUser.objects.filter(id=data.get("user_id")).first()

            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_204_NO_CONTENT)

            friends = find_user_friends(data.get("user_id"))

            if friends:
                serialized = TaggUserSerializer(friends, many=True)
                return get_response(data=serialized.data, type=200)

            else:
                return get_response(data=[], type=204)

        except TaggUser.DoesNotExist:
            self.logger.exception("User does not exist")
            return get_response(data="User does not exist", type=400)

        except Friends.DoesNotExist:
            self.logger.exception("No results found")
            return get_response(data="No results found", type=400)

        except Exception as err:
            self.logger.exception("Problem fetching the friends list", err.args)
            return get_response(data="Problem fetching the friends list", type=500)
