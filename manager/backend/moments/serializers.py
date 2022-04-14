from rest_framework import serializers

from ..serializers import TaggUserSerializer
from .comments.utils import get_moment_comments_count
from .models import Moment
from .shares.models import MomentShares
from .views.models import MomentViews


class MomentSerializer(serializers.ModelSerializer):
    view_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()

    class Meta:
        model = Moment
        fields = [
            "moment_id",
            "caption",
            "date_created",
            "moment_url",
            "moment_category",
            "thumbnail_url",
            "view_count",
            "share_count",
        ]

    def get_view_count(self, obj):
        return MomentViews.objects.filter(moment_viewed=obj.moment_id).count()

    def get_share_count(self, obj):
        return MomentShares.objects.filter(moment_shared=obj.moment_id).count()


class MomentPostSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()
    # added "user" here since "user_id" is a bad variable name
    user = serializers.SerializerMethodField()

    class Meta:
        model = Moment
        fields = [
            "moment_id",
            "caption",
            "date_created",
            "moment_url",
            "moment_category",
            "thumbnail_url",
            "view_count",
            "share_count",
            "comments_count",
            "user",
        ]

    def get_comments_count(self, obj):
        if not self.context.get("user"):
            raise NotImplementedError("user context is required")
        return get_moment_comments_count(obj.moment_id, self.context.get("user"))

    def get_user(self, obj):
        return TaggUserSerializer(obj.user_id).data

    def get_view_count(self, obj):
        return MomentViews.objects.filter(moment_viewed=obj.moment_id).count()

    def get_share_count(self, obj):
        return MomentShares.objects.filter(moment_shared=obj.moment_id).count()


class PublicMomentPostSerializer(MomentPostSerializer):
    def get_comments_count(self, obj):
        return get_moment_comments_count(obj.moment_id, None)


# consider banner_info serializer - TODO -
# use this class later when we need to work on the discover moments banner
class MomentBannerInfoSerializer(serializers.ModelSerializer):
    comments_count = serializers.SerializerMethodField()
    comment_preview = serializers.SerializerMethodField()
    banner_info = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()

    class Meta:
        model = Moment
        fields = [
            "moment_id",
            "caption",
            "date_created",
            "moment_url",
            "moment_category",
            "thumbnail_url",
            "comments_count",
            "comment_preview",
            "view_count",
        ]

    def get_comments_count(self, obj):
        if not self.context.get("user"):
            raise NotImplementedError("user context is required")
        return get_moment_comments_count(obj.moment_id, self.context.get("user"))

    def get_view_count(self, obj):
        return MomentViews.objects.filter(moment_viewed=obj.moment_id).count()


class MomentAndUserSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    view_count = serializers.SerializerMethodField()
    share_count = serializers.SerializerMethodField()

    class Meta:
        model = Moment
        fields = "__all__"

    def get_user(self, obj):
        return TaggUserSerializer(obj.user_id).data

    def get_view_count(self, obj):
        return MomentViews.objects.filter(moment_viewed=obj.moment_id).count()

    def get_share_count(self, obj):
        return MomentShares.objects.filter(moment_shared=obj.moment_id).count()
