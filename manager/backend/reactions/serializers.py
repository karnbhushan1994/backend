from rest_framework import serializers

from .models import CommentsReactionList, CommentThreadsReactionList
from ..serializers import TaggUserSerializer
from ..models import TaggUser


class CommentsReactionListSerializer(serializers.ModelSerializer):
    actor = TaggUserSerializer()

    class Meta:
        model = CommentsReactionList
        fields = ["actor"]


class CommentThreadsReactionListSerializer(serializers.ModelSerializer):
    actor = TaggUserSerializer()

    class Meta:
        model = CommentThreadsReactionList
        fields = ["actor"]
