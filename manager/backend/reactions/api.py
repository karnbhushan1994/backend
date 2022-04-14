import logging
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..common import validator
from ..common.notification_manager import handle_notification
from ..models import BlockedUser
from ..moments.comments.models import CommentThreads, MomentComments
from ..profile.utils import allow_to_view_private_content
from .models import (
    CommentsReactionList,
    CommentThreadsReactionList,
    Reaction,
    ReactionType,
)
from .serializers import (
    CommentsReactionListSerializer,
    CommentThreadsReactionListSerializer,
)


class CommentReactionsListViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(CommentReactionsListViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """Create a user reaction for a comment in the CommentsReactionList table

        Args:
            comment_id : (str) The comment_id to which the request user is reacting to
            reaction_type : (str) The reaction type to be stored [LIKE, etc..]

        Returns:
              A response object with appropriate reponse status
        """
        try:
            data = request.POST
            if not validator.check_is_valid_parameter("comment_id", data):
                return validator.get_response(data="comment_id is required", type=400)
            if not validator.check_is_valid_parameter("reaction_type", data):
                return validator.get_response(
                    data="reaction_type is required", type=400
                )

            actor = request.user
            comment_id = data.get("comment_id")
            reaction_type = data.get("reaction_type")

            # Check if comment exists
            if not MomentComments.objects.filter(comment_id=comment_id).exists():
                return validator.get_response(data="Comment does not exist", type=404)

            # Retrieve comment object
            comment = MomentComments.objects.filter(comment_id=comment_id).first()
            commenter = comment.commenter

            # Check if commenter account is private
            if not allow_to_view_private_content(actor, commenter):
                return validator.get_response(
                    data="Commenter account is private", type=403
                )

            # Check if moment poster account is private
            moment = comment.moment_id
            moment_poster = moment.user_id
            if not allow_to_view_private_content(actor, moment_poster):
                return validator.get_response(
                    data="Moment poster account is private", type=403
                )

            # Check if commenter has blocked the user, to prevent user from liking their comment
            if BlockedUser.objects.filter(blocker=commenter, blocked=actor).exists():
                return validator.get_response(data="Commenter blocked user", type=403)

            # Check if user's reaction already exists for comment
            reactions_list = Reaction.objects.filter(reaction_object_id=comment_id)
            reaction = None
            for item in reactions_list:
                # Check if reaction already exists, retrieve existing reaction
                if item.reaction_type == reaction_type:
                    reaction = item
                # Check if user already reacted with reaction
                if CommentsReactionList.objects.filter(
                    reaction=item, actor=actor
                ).exists():
                    return validator.get_response(
                        data="User reaction already exists", type=403
                    )

            # Create a new reaction if not found
            if reaction == None:
                reaction = Reaction.objects.create(
                    object=comment,
                    reaction_object_id=comment.comment_id,
                    reaction_type=reaction_type,
                    timestamp=datetime.now(),
                )
                reaction.save()

            # Create a new user reaction
            new_listreaction = CommentsReactionList.objects.create(
                reaction=reaction, actor=actor
            )
            new_listreaction.save()

            # Notify the commenter of a new reaction from other users
            if commenter != actor:
                if reaction.reaction_type == ReactionType.LIKE:
                    verbage = "Liked your comment!"
                else:
                    verbage = "Reacted to your comment!"
                handle_notification(
                    notification_type="CMT",
                    actor=actor,
                    receiver=commenter,
                    verbage=verbage,
                    notification_object=comment,
                )

            to_return = {
                "reaction_id": str(reaction.id),
                "date_created": str(reaction.timestamp),
            }
            return validator.get_response(data=to_return, type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem validating details")
            return validator.get_response(
                data="There was a problem validating details", type=500
            )

        except Exception as err:
            self.logger.exception("There was a problem trying to post the reaction")
            return validator.get_response(
                data="There was a problem trying to post the reaction", type=500
            )

    def list(self, request):
        """List of TaggUsers who reacted to the comment

        Args:
            comment_id: Id of comment for which reaction have to be retrieved

        Returns:
            A response object with list of tagg users for every reaction type

        """
        try:
            data = request.query_params
            user = request.user

            if not validator.check_is_valid_parameter("comment_id", data):
                return validator.get_response(data="comment_id is required", type=400)

            comment_id = data.get("comment_id")

            # Check if comment exists
            if not MomentComments.objects.filter(comment_id=comment_id).exists():
                return validator.get_response(data="Comment does not exist", type=404)

            comment = MomentComments.objects.filter(comment_id=comment_id).first()

            # Check if request user has permission to view reactions list
            if BlockedUser.objects.filter(
                blocker=comment.commenter, blocked=user
            ).exists():
                return validator.get_response(data="Commenter blocked user", type=403)

            # Check if at least one reaction exists for comment id
            if not Reaction.objects.filter(reaction_object_id=comment_id).exists():
                return validator.get_response(
                    data="No reaction exists for comment", type=400
                )

            # Retieve list of reactions for comment
            reaction_list = Reaction.objects.filter(reaction_object_id=comment_id)

            response = []

            # For every reaction, retrieve TaggUsers and add to response object
            for reaction in reaction_list:
                user_reaction_list = CommentsReactionList.objects.filter(
                    Q(reaction=reaction), ~Q(actor__blocked__blocker=user.id)
                )

                serializer_response = CommentsReactionListSerializer(
                    user_reaction_list, many=True
                ).data

                response.append(
                    {
                        "reaction": reaction.reaction_type,
                        "user_list": [o["actor"] for o in serializer_response],
                    }
                )

            return validator.get_response(data=response, type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem validating details")
            return validator.get_response(
                data="There was a problem validating details", type=500
            )

        except Exception as err:
            self.logger.exception("There was a problem trying to fetch user reactions")
            return validator.get_response(
                data="There was a problem trying to fetch user reactions", type=500
            )

    def destroy(self, request, pk=None):
        """Delete a reaction for a user reaction

        Args:
            comment_id (pk) : Comment id for which the reaction must be deleted for the request user
            reaction_type (query params) : reaction_type that must be deleted
        Returns:
              A response with appropriate delete success status
        """
        try:

            actor = request.user
            comment_id = pk
            data = request.query_params

            if not validator.check_is_valid_parameter("reaction_type", data):
                return validator.get_response(
                    data="reaction_type is required", type=400
                )

            reaction_type = data.get("reaction_type")

            # Check if the reaction exists
            if not Reaction.objects.filter(
                reaction_object_id=comment_id, reaction_type=reaction_type
            ).exists():
                return validator.get_response(data="Reaction does not exist", type=400)

            reaction = Reaction.objects.filter(
                reaction_object_id=comment_id, reaction_type=reaction_type
            ).first()

            # Check if the user reacted to comment
            if not CommentsReactionList.objects.filter(
                actor=actor, reaction=reaction
            ).exists():
                return validator.get_response(
                    data="User did not react to comment", type=400
                )

            # Retrieve user's reaction
            user_reaction = CommentsReactionList.objects.filter(
                actor=actor, reaction=reaction
            ).first()

            # Delete user's reaction
            user_reaction.delete()

            # Check number of users that posted that reaction, delete reaction if count = 0
            reaction_count = CommentsReactionList.objects.filter(
                reaction=reaction
            ).count()
            if reaction_count == 0:
                Reaction.objects.filter(
                    reaction_object_id=comment_id, reaction_type=reaction_type
                ).delete()

            return validator.get_response(data="Success, reaction deleted", type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem validating details")
            return validator.get_response(
                data="There was a problem validating details", type=500
            )

        except Exception as err:
            self.logger.exception("There was a problem trying to delete the reaction")
            return validator.get_response(
                data="There was a problem trying to delete the reaction", type=500
            )


class CommentThreadsReactionsListViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(CommentThreadsReactionsListViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """Create a user reaction for a reply in the CommentThreadsReactionList table

        Args:
            comment_id : (str) The reply id to which the request user is reacting to
            reaction_type : (str) The reaction type to be stored [LIKE, etc..]

        Returns:
              A response object with appropriate reponse status
        """
        try:
            data = request.POST
            if not validator.check_is_valid_parameter("comment_id", data):
                return validator.get_response(data="comment_id is required", type=400)
            if not validator.check_is_valid_parameter("reaction_type", data):
                return validator.get_response(
                    data="reaction_type is required", type=400
                )

            actor = request.user
            comment_id = data.get("comment_id")
            reaction_type = data.get("reaction_type")

            # Check if reply exists
            if not CommentThreads.objects.filter(comment_id=comment_id).exists():
                return validator.get_response(data="Reply does not exist", type=404)

            # Retrieve reply object
            comment = CommentThreads.objects.filter(comment_id=comment_id).first()
            commenter = comment.commenter

            # Check if reply owner's account is private
            if not allow_to_view_private_content(actor, commenter):
                return validator.get_response(
                    data="Reply owner account is private", type=403
                )

            # Check if parent comment owner's account is private
            parent_commenter = comment.parent_comment.commenter
            if not allow_to_view_private_content(actor, parent_commenter):
                return validator.get_response(
                    data="Parent comment owner account is private", type=403
                )

            # Check if moment poster account is private
            moment = comment.parent_comment.moment_id
            moment_poster = moment.user_id
            if not allow_to_view_private_content(actor, moment_poster):
                return validator.get_response(
                    data="Moment poster account is private", type=403
                )

            # Check if commenter has blocked the user, to prevent user from liking their reply
            if BlockedUser.objects.filter(
                blocker__in=[commenter, parent_commenter, moment_poster], blocked=actor
            ).exists():
                return validator.get_response(data="Commenter blocked user", type=403)

            # Check if user's reaction already exists for comment
            reactions_list = Reaction.objects.filter(reaction_object_id=comment_id)
            reaction = None
            for item in reactions_list:
                # Check if reaction already exists, retrieve existing reaction
                if item.reaction_type == reaction_type:
                    reaction = item
                # Check if user already reacted with reaction
                if CommentThreadsReactionList.objects.filter(
                    reaction=item, actor=actor
                ).exists():
                    return validator.get_response(
                        data="User reaction already exists", type=403
                    )

            # Create a new reaction if not found
            if reaction == None:
                reaction = Reaction.objects.create(
                    object=comment,
                    reaction_object_id=comment.comment_id,
                    reaction_type=reaction_type,
                    timestamp=datetime.now(),
                )
                reaction.save()

            # Create a new user reaction
            new_listreaction = CommentThreadsReactionList.objects.create(
                reaction=reaction, actor=actor
            )
            new_listreaction.save()

            # Notify the reply owner of a new reaction from other users
            if commenter != actor:
                if reaction.reaction_type == ReactionType.LIKE:
                    verbage = "Liked your comment!"
                else:
                    verbage = "Reacted to your comment!"
                handle_notification(
                    notification_type="CMT",
                    actor=actor,
                    receiver=commenter,
                    verbage=verbage,
                    notification_object=comment,
                )

            to_return = {
                "reaction_id": str(reaction.id),
                "date_created": str(reaction.timestamp),
            }
            return validator.get_response(data=to_return, type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem validating details")
            return validator.get_response(
                data="There was a problem validating details", type=500
            )

        except Exception as err:
            self.logger.exception("There was a problem trying to post the reaction")
            return validator.get_response(
                data="There was a problem trying to post the reaction", type=500
            )

    def list(self, request):
        """List of TaggUsers who reacted to the reply

        Args:
            comment_id: Id of reply for which reaction has to be retrieved

        Returns:
            A response object with list of tagg users for every reaction type

        """
        try:
            data = request.query_params
            user = request.user

            if not validator.check_is_valid_parameter("comment_id", data):
                return validator.get_response(data="comment_id is required", type=400)

            comment_id = data.get("comment_id")

            # Check if reply exists
            if not CommentThreads.objects.filter(comment_id=comment_id).exists():
                return validator.get_response(data="Reply does not exist", type=404)

            reply = CommentThreads.objects.filter(comment_id=comment_id).first()

            # Check if request user has permission to view reactions list
            if BlockedUser.objects.filter(
                blocker=reply.commenter, blocked=user
            ).exists():
                return validator.get_response(data="Commenter blocked user", type=403)

            # Check if at least one reaction exists for comment id
            if not Reaction.objects.filter(reaction_object_id=comment_id).exists():
                return validator.get_response(
                    data="Reaction does not exist for comment", type=400
                )

            # Retieve list of reactions for comment
            reaction_list = Reaction.objects.filter(reaction_object_id=comment_id)

            response = []

            # For every reaction, retrieve TaggUsers and add to response object
            for reaction in reaction_list:
                user_reaction_list = CommentThreadsReactionList.objects.filter(
                    Q(reaction=reaction), ~Q(actor__blocked__blocker=user.id)
                )

                serializer_response = CommentThreadsReactionListSerializer(
                    user_reaction_list, many=True
                ).data

                response.append(
                    {
                        "reaction": reaction.reaction_type,
                        "user_list": [o["actor"] for o in serializer_response],
                    }
                )

            return validator.get_response(data=response, type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem validating details")
            return validator.get_response(
                data="There was a problem validating details", type=500
            )

        except Exception as err:
            self.logger.exception("There was a problem trying to fetch user reactions")
            return validator.get_response(
                data="There was a problem trying to fetch user reactions", type=500
            )

    def destroy(self, request, pk=None):
        """Delete a reaction for a user reaction

        Args:
            comment_id (pk) : Reply id for which the reaction must be deleted for the request user
            reaction_type (query params) : reaction_type that must be deleted
        Returns:
              A response with appropriate delete success status
        """
        try:

            actor = request.user
            comment_id = pk
            data = request.query_params

            if not validator.check_is_valid_parameter("reaction_type", data):
                return validator.get_response(
                    data="reaction_type is required", type=400
                )

            reaction_type = data.get("reaction_type")

            # Check if the reaction exists
            if not Reaction.objects.filter(
                reaction_object_id=comment_id, reaction_type=reaction_type
            ).exists():
                return validator.get_response(
                    data="Reaction object does not exist", type=400
                )

            reaction = Reaction.objects.filter(
                reaction_object_id=comment_id, reaction_type=reaction_type
            ).first()

            # Check if the user reacted to reply
            if not CommentThreadsReactionList.objects.filter(
                actor=actor, reaction=reaction
            ).exists():
                return validator.get_response(
                    data="User did not react to reply", type=400
                )

            # Retrieve user's reaction
            user_reaction = CommentThreadsReactionList.objects.filter(
                actor=actor, reaction=reaction
            ).first()

            # Delete user's reaction
            user_reaction.delete()

            # Check number of users that posted that reaction, delete reaction if count = 0
            reaction_count = CommentThreadsReactionList.objects.filter(
                reaction=reaction
            ).count()
            if reaction_count == 0:
                Reaction.objects.filter(
                    reaction_object_id=comment_id, reaction_type=reaction_type
                ).delete()

            return validator.get_response(data="Success, reaction deleted", type=200)

        except ValidationError as err:
            self.logger.exception("There was a problem validating details")
            return validator.get_response(
                data="There was a problem validating details", type=500
            )

        except Exception as err:
            self.logger.exception("There was a problem trying to delete the reaction")
            return validator.get_response(
                data="There was a problem trying to delete the reaction", type=500
            )
