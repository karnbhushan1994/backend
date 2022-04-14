from django.db.models.query_utils import Q

from rest_framework import serializers

from ...reactions.models import (
    CommentsReactionList,
    CommentThreadsReactionList,
    Reaction,
)
from ..serializers import MomentAndUserSerializer, TaggUserSerializer
from ..models import Moment
from .models import MomentComments, CommentThreads


class CommentNotificationSerializer(serializers.ModelSerializer):
    notification_data = serializers.SerializerMethodField()

    class Meta:
        model = MomentComments
        fields = ["notification_data", "comment_id"]

    def get_notification_data(self, obj):
        return MomentAndUserSerializer(
            Moment.objects.filter(moment_id=obj.moment_id_id).first()
        ).data


class ThreadNotificationSerializer(serializers.ModelSerializer):
    notification_data = serializers.SerializerMethodField()

    class Meta:
        model = CommentThreads
        fields = ["comment_id", "parent_comment", "notification_data"]

    def get_notification_data(self, obj):
        return MomentAndUserSerializer(
            Moment.objects.filter(moment_id=obj.parent_comment.moment_id_id).first()
        ).data


class MomentCommentsSerializer(serializers.ModelSerializer):
    commenter = TaggUserSerializer()
    replies_count = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    reaction_count = serializers.SerializerMethodField()

    class Meta:
        model = MomentComments
        fields = [
            "comment_id",
            "comment",
            "date_created",
            "commenter",
            "moment_id",
            "replies_count",
            "user_reaction",
            "reaction_count",
        ]

    def get_replies_count(self, obj):
        return CommentThreads.objects.filter(parent_comment=obj.comment_id).count()

    def get_user_reaction(self, obj):
        # Retrieve all reactions for comment
        if Reaction.objects.filter(reaction_object_id=obj.comment_id).exists():
            reaction_list = Reaction.objects.filter(reaction_object_id=obj.comment_id)

            # Retrieve user's reaction from list of reactions for comment
            if CommentsReactionList.objects.filter(
                reaction__in=reaction_list, actor=self.context.get("user")
            ).exists():
                user_reaction = CommentsReactionList.objects.filter(
                    reaction__in=reaction_list, actor=self.context.get("user")
                ).first()

                return {
                    "id": user_reaction.reaction.id,
                    "type": user_reaction.reaction.reaction_type,
                }

        return None

    def get_reaction_count(self, obj):
        # Retrieve list of reactions for comment_id
        reactions_list = Reaction.objects.filter(reaction_object_id=obj.comment_id)

        # Retrieve the count of users for each reaction in list except blocked users
        count = 0
        for reaction in reactions_list:
            count += CommentsReactionList.objects.filter(
                Q(reaction=reaction),
                ~Q(actor__blocked__blocker=self.context.get("user").id),
            ).count()

        return count


class CommentThreadsSerializer(serializers.ModelSerializer):
    commenter = TaggUserSerializer()
    parent_comment = MomentCommentsSerializer()
    user_reaction = serializers.SerializerMethodField()
    reaction_count = serializers.SerializerMethodField()

    class Meta:
        model = CommentThreads
        fields = [
            "comment_id",
            "comment",
            "date_created",
            "commenter",
            "parent_comment",
            "user_reaction",
            "reaction_count",
        ]

    def get_user_reaction(self, obj):
        # Retrieve all reactions for comment
        if Reaction.objects.filter(reaction_object_id=obj.comment_id).exists():
            reaction_list = Reaction.objects.filter(reaction_object_id=obj.comment_id)

            # Retrieve user's reaction from list of reactions for reply
            if CommentThreadsReactionList.objects.filter(
                reaction__in=reaction_list, actor=self.context.get("user")
            ).exists():
                user_reaction = CommentThreadsReactionList.objects.filter(
                    reaction__in=reaction_list, actor=self.context.get("user")
                ).first()

                return {
                    "id": user_reaction.reaction.id,
                    "type": user_reaction.reaction.reaction_type,
                }

        return None

    def get_reaction_count(self, obj):
        # Retrieve list of reactions for comment_id
        reactions_list = Reaction.objects.filter(reaction_object_id=obj.comment_id)

        # Retrieve the count of users for each reaction in list except blocked users
        count = 0
        for reaction in reactions_list:
            count += CommentThreadsReactionList.objects.filter(
                Q(reaction=reaction),
                ~Q(actor__blocked__blocker=self.context.get("user").id),
            ).count()

        return count
