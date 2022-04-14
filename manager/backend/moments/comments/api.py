import datetime
import logging

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import response
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ...notifications.models import Notification

from ..utils import increase_moment_score

from ...models import BlockedUser

from ...common import validator
from ...common.notification_manager import handle_notification
from ...common.validator import check_is_valid_parameter, get_response
from ...gamification.constants import TAGG_SCORE_ALLOTMENT
from ...gamification.utils import TaggScoreUpdateException, increase_tagg_score
from ...notifications.utils import notify_mentioned_users
from ...profile.utils import allow_to_view_private_content
from ..models import Moment, MomentScoreWeights, TaggUser
from .models import CommentThreads, MomentComments, NewCommentStatus
from .serializers import CommentThreadsSerializer, MomentCommentsSerializer
from .utils import get_moment_comments_count, is_acceptable_comment_length


class MomentCommentsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(MomentCommentsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """Takes in a moment id, commenter and comment and updates the MomentComments tabel

        Args:
            moment_id : (str)
            commenter : (str)
            comment : (str) The comment to be stored

        Returns:
              A response object with appropriate reponse status
        """
        data = request.POST
        if not check_is_valid_parameter("moment_id", data):
            return validator.get_response(data="moment_id is required", type=400)

        if not check_is_valid_parameter("comment", data):
            return validator.get_response(data="comment is required", type=400)

        flag=False
        moment_id = data.get("moment_id")
        commenter = request.user
        comment = data.get("comment")

        # if not is_acceptable_comment_length(comment):
        #     return validator.Response(data='Comment exceeds character limit', type=406)

        try:
            moment = Moment.objects.filter(moment_id=moment_id).first()
            moment_user_id = moment.user_id_id
            if not moment:
                return validator.get_response(data="Moment does not exist", type=404)

            # Prevent unauthorized user from commenting on user's moment
            user = TaggUser.objects.filter(id=moment_user_id).first()
            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_403_FORBIDDEN)

            if (
                BlockedUser.objects.filter(
                    blocked=moment.user_id, blocker=commenter
                ).exists()
                or BlockedUser.objects.filter(
                    blocked=commenter, blocker=moment.user_id
                ).exists()
            ):
                return Response(
                    "Blocker or blocked user cannot comment on moment",
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Increase tagg score for comment on a moment
            if commenter != moment.user_id:
                increase_tagg_score(commenter, TAGG_SCORE_ALLOTMENT["MOMENT_COMMENT"])

            # Join community Pop up functionality. tma-1861
            if commenter != moment.user_id:
                momentCommentsObj = NewCommentStatus.objects.filter(commenter=commenter).exists()
                # Flag set to False: Do not show popup to User if Flag is False.
                if momentCommentsObj == False:
                    logging.info('New comment for user show Join community Pop Up')
                    #Flag set to True: show pop up to User if Flag is True.
                    flag = True
                    new_user_comment = NewCommentStatus.objects.create(
                    commenter=commenter,
                    flag=flag,
                    )
                    new_user_comment.save()



            new_comment = MomentComments.objects.create(
                commenter=commenter,
                moment_id=moment,
                comment=comment,
                date_created=datetime.datetime.now(),
            )
            new_comment.save()

            if new_comment:
                increase_moment_score(moment, MomentScoreWeights.COMMENT.value)

            # Notifying the moment's owner of the comment
            if moment.user_id != commenter:
                handle_notification(
                    notification_type="CMT",
                    actor=commenter,
                    receiver=moment.user_id,
                    verbage="Commented on your moment!",
                    notification_object=new_comment,
                )

            # Notify mentioned users
            notify_mentioned_users(
                notification_type="CMT",
                mentioned_verbage=comment,
                notification_verbage="Mentioned you in a comment!",
                actor=commenter,
                notification_object=new_comment,
            )

            to_return = {
                "comment_id": str(new_comment.comment_id),
                "date_created": str(new_comment.date_created),
                "show_community_pop_up": flag
            }
            return validator.get_response(data=to_return, type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem fetching the user details")
            return validator.get_response(
                data="There was a problem fetching the user details", type=500
            )
        except TaggScoreUpdateException as err:
            self.logger.exception("Tagg score update exception")
            return validator.get_response(data="Tagg score update exception", type=500)
        except Exception as err:
            self.logger.exception("There was a problem trying to post the comment")
            return validator.get_response(
                data="There was a problem trying to post the comment", type=500
            )

    def list(self, request):
        """Takes in a moment id and returns details about all the comments posted on that moment

        Args:
            moment_id : (str)

        Returns:
            A list of comments on the moment with each comment having the following values
            ['comment_id', 'comment', 'date_created','commenter__id','commenter__username']
        """
        data = request.query_params
        if not check_is_valid_parameter("moment_id", data):
            return validator.get_response(data="moment_id is required", type=400)

        moment_id = data.get("moment_id")

        try:
            moment = Moment.objects.filter(moment_id=moment_id).first()

            # Prevent unauthorized user from reading comments on user's moment
            user = TaggUser.objects.filter(id=moment.user_id_id).first()
            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_403_FORBIDDEN)

            if not moment:
                return validator.get_response(data="Moment does not exist", type=404)

            # User should not be able to view comments of the user they are blocked by
            comments = MomentComments.objects.filter(
                Q(moment_id=moment_id),
                ~Q(commenter__blocker__blocked=request.user),
                ~Q(commenter__blocked__blocker=request.user),
            )

            # Serialize objects to be returned
            serialized = MomentCommentsSerializer(
                comments, many=True, context={"user": request.user}
            )
            return validator.get_response(data=serialized.data, type=200)

        except ValidationError as err:
            self.logger.exception(
                "There was a problem fetching the moment details, maybe it does not exist"
            )
            return validator.get_response(
                data="There was a problem fetching the moment details, maybe it does not exist",
                type=500,
            )
        except Exception as err:
            self.logger.exception("There was a problem trying to retrieve the comments")
            return validator.get_response(
                data="There was a problem trying to retrieve the comments", type=500
            )

    def retrieve(self, request, pk):
        """Takes in a moment id and returns count of the comments on this moment

        Args:
            moment_id (pk): (str)

        Returns:
            Count of the number of comments on this moment
        """
        try:
            moment = Moment.objects.filter(moment_id=pk).first()

            # Prevent unauthorized user from retrieving count od comments on user's moment
            user = TaggUser.objects.filter(id=moment.user_id_id).first()
            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_403_FORBIDDEN)

            if not moment:
                return validator.get_response(data="Moment does not exist", type=404)

            return Response({"count": get_moment_comments_count(moment, request.user)})

        except ValidationError as err:
            self.logger.exception(
                "There was a problem fetching the moment details, maybe it does not exist"
            )
            return validator.get_response(
                data="There was a problem fetching the moment details, maybe it does not exist",
                type=500,
            )
        except Exception as err:
            self.logger.exception("There was a problem trying to retrieve the comments")
            return validator.get_response(
                data="There was a problem trying to retrieve the comments", type=500
            )

    def destroy(self, request, pk=None):
        """Deletes a comment

        Args:
            comment_id (pk): (str) Id of the comment to be deleted
        Returns:
            Status of action
        """
        try:
            # Check if comment exists
            if MomentComments.objects.filter(comment_id=pk).exists():
                comment = MomentComments.objects.get(comment_id=pk)

                # check if requesting user and owner of reply is the same, or is the moment owner
                moment = Moment.objects.filter(moment_id=comment.moment_id_id).first()
                if request.user != comment.commenter and request.user != moment.user_id:
                    return get_response(data="Unauthorised action", type=401)

                comment.delete()
                return get_response(data="Success, comment deleted", type=200)

            else:
                raise MomentComments.DoesNotExist()

            return get_response(data="Something went wrong", type=400)

        except MomentComments.DoesNotExist:
            self.logger.error("Comment does not exist")
            return get_response(data="Comment does not exist", type=400)
        except Exception as err:
            self.logger.exception("There was a problem with deleting the comment")
            return get_response(
                data="There was a problem with deleting the comment", type=500
            )

    serializer_class = MomentCommentsSerializer



class CommentThreadsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(CommentThreadsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """Created a record for a reply in the CommentThreads table

        Args:
            comment_id : (str) The comment to which the request user is replying to
            comment : (str) The comment to be stored

        Returns:
              A response object with appropriate reponse status
        """
        try:
            data = request.POST
            if not check_is_valid_parameter("comment_id", data):
                return validator.get_response(data="comment_id is required", type=400)

            if not check_is_valid_parameter("comment", data):
                return validator.get_response(data="comment is required", type=400)

            commenter = request.user
            comment_id = data.get("comment_id")
            comment = data.get("comment")

            if not is_acceptable_comment_length(comment):
                return validator.Response(
                    data="Reply exceeds character limit", type=406
                )

            parent_comment = MomentComments.objects.filter(
                comment_id=comment_id
            ).first()

            # Prevent unauthorized user from replying to a comment on user's moment
            moment = Moment.objects.filter(
                moment_id=parent_comment.moment_id_id
            ).first()
            moment_user = TaggUser.objects.filter(id=moment.user_id_id).first()
            if not allow_to_view_private_content(request.user, moment_user):
                return Response("Account is private", 403)

            if not parent_comment:
                return validator.get_response(data="Comment does not exist", type=404)

            new_reply = CommentThreads.objects.create(
                parent_comment=parent_comment,
                commenter=commenter,
                comment=comment,
                date_created=datetime.datetime.now(),
            )
            status = new_reply.save()

            if status:
                increase_moment_score(moment, MomentScoreWeights.COMMENT.value)

            # Increase tagg score for reply to a comment on a moment
            if commenter != moment.user_id and commenter != parent_comment.commenter:
                increase_tagg_score(commenter, TAGG_SCORE_ALLOTMENT["MOMENT_COMMENT"])

            # Notifying the moment owner of a new reply from other users
            if moment_user != commenter:
                handle_notification(
                    notification_type="CMT",
                    actor=commenter,
                    receiver=moment_user,
                    verbage="Replied to a comment on your moment!",
                    notification_object=new_reply,
                )

            # Notifying mentioned users in reply
            notified_users = notify_mentioned_users(
                notification_type="CMT",
                mentioned_verbage=comment,
                notification_verbage="Mentioned you in a comment!",
                actor=commenter,
                notification_object=new_reply,
            )

            # Notifying the parent_comment user of a new reply from other users
            if (
                commenter != parent_comment.commenter
                and parent_comment.commenter not in notified_users
            ):
                handle_notification(
                    notification_type="CMT",
                    actor=commenter,
                    receiver=parent_comment.commenter,
                    verbage="Replied to your comment!",
                    notification_object=new_reply,
                )

            to_return = {
                "comment_id": str(new_reply.comment_id),
                "date_created": str(new_reply.date_created),
            }
            return validator.get_response(data=to_return, type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem fetching the user details")
            return validator.get_response(
                data="There was a problem fetching the user details", type=500
            )
        except Exception as err:
            self.logger.exception("There was a problem trying to post the comment")
            return validator.get_response(
                data="There was a problem trying to post the comment", type=500
            )

    def list(self, request):
        """Returns the replies to a specific comment

        Args:
            comment_id : (str) Id of the comment for which replies are requested

        Returns:
            A list of comments on the moment with each comment having the following values
            ['comment_id', 'comment', 'date_created','commenter__id','commenter__username']
        """
        data = request.query_params
        if not check_is_valid_parameter("comment_id", data):
            return validator.get_response(data="comment_id is required", type=400)

        parent_comment_id = data.get("comment_id")

        try:
            parent_comment = MomentComments.objects.filter(
                comment_id=parent_comment_id
            ).first()

            moment = Moment.objects.filter(
                moment_id=parent_comment.moment_id_id
            ).first()
            user = TaggUser.objects.filter(id=moment.user_id_id).first()

            # Prevent unauthorized user from reading replie to a comment on user's moment
            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_403_FORBIDDEN)

            if not parent_comment:
                return validator.get_response(data="Comment does not exist", type=404)

            # Prevent unauthorized user from viewing comments by users they are blocked by
            comment_thread = CommentThreads.objects.filter(
                Q(parent_comment=parent_comment),
                ~Q(commenter__blocker__blocked=request.user),
            )

            # Serialize objects to be returned
            serialized = CommentThreadsSerializer(
                comment_thread, many=True, context={"user": request.user}
            )
            return validator.get_response(data=serialized.data, type=200)

        except ValidationError as err:
            self.logger.exception(
                "There was a problem fetching the comment details, maybe it does not exist"
            )
            return validator.get_response(
                data="There was a problem fetching the comment details, maybe it does not exist",
                type=500,
            )
        except Exception as err:
            self.logger.exception("There was a problem trying to retrieve the comments")
            return validator.get_response(
                data="There was a problem trying to retrieve the comments", type=500
            )

    def retrieve(self, request, pk):
        """Returns count of the replies for the comment

        Args:
            comment_id (pk): (str) Id of the comment who's no of replies are requested for

        Returns:
            Count of the number of replies to the comment
        """
        try:
            parent_comment = MomentComments.objects.filter(comment_id=pk).first()

            # Prevent unauthorized user from retrieving count of replies to a comment on user's moment
            moment = Moment.objects.filter(
                moment_id=parent_comment.moment_id_id
            ).first()
            user = TaggUser.objects.filter(id=moment.user_id_id).first()
            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_403_FORBIDDEN)

            if not parent_comment:
                return validator.get_response(data="Comment does not exist", type=404)

            # User should not be able to view comments of the user they are blocked by
            comment_thread_length = CommentThreads.objects.filter(
                Q(parent_comment=parent_comment),
                ~Q(commenter__blocker__blocked=request.user),
            ).count()

            to_return = {"count": str(comment_thread_length)}
            return validator.get_response(data=to_return, type=200)

        except ValidationError as err:
            self.logger.exception(
                "There was a problem fetching the moment details, maybe it does not exist"
            )
            return validator.get_response(
                data="There was a problem fetching the moment details, maybe it does not exist",
                type=500,
            )
        except Exception as err:
            self.logger.exception("There was a problem trying to retrieve the comments")
            return validator.get_response(
                data="There was a problem trying to retrieve the comments", type=500
            )

    def destroy(self, request, pk):
        """Deletes a reply to a comment

        Args:
            comment_id (pk): (str) Id of the reply to be deleted
        Returns:
            Status of action
        """

        try:
            # Check if comment exists and needed components are there
            if CommentThreads.objects.filter(comment_id=pk).exists():
                reply = CommentThreads.objects.get(comment_id=pk)
                if MomentComments.objects.filter(comment_id=reply.parent_comment.comment_id).exists():
                    comment = MomentComments.objects.get(comment_id=reply.parent_comment.comment_id)
                    if Moment.objects.filter(moment_id=comment.moment_id_id).exists():
                        moment = Moment.objects.get(moment_id=comment.moment_id_id)
                        # check if requesting user and owner of reply is the same, or is the moment owner
                        if request.user != reply.commenter and request.user != moment.user_id:
                            return get_response(data="Unauthorised action", type=401)
                        reply.delete()
                        return get_response(data="Success, reply deleted", type=200)
                    else:
                        raise Moment.DoesNotExist()
                else:
                    raise MomentComments.DoesNotExist()
            else:
                raise CommentThreads.DoesNotExist()

            return get_response(data="Something went wrong", type=400)

        except CommentThreads.DoesNotExist:
            self.logger.error("Reply does not exist")
            return get_response(data="Reply does not exist", type=400)
        except Exception as err:
            self.logger.exception("There was a problem with deleting the reply")
            return get_response(
                data="There was a problem with deleting the reply", type=500
            )

    serializer_class = CommentThreadsSerializer
