import functools

from django.db.models.query_utils import Q
from rest_framework import serializers

from ..common.constants import HOMEPAGE
from ..gamification.constants import GAMIFICATION_TIER_DATA, GamificationTier
from ..common.image_manager import (
    header_pic_url,
    profile_pic_url,
    profile_thumbnail_url,
)
from ..friends.utils import get_user_friend_count
from ..models import TaggUser
from ..moments.comments.models import MomentComments
from ..moments.models import Moment
from ..moments.moment_category.utils import get_moment_categories
from ..reactions.models import CommentsReactionList
from ..serializers import TaggUserSerializer
from ..skins.models import Skin
from ..skins.serializers import SkinSerializer
from ..widget.models import Widget
from ..widget.serializers import WidgetSerializer
from ..models import TaggUser
from ..gamification.models import GameProfile


class WebUserSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()
    profile_pic = serializers.SerializerMethodField()
    header_pic = serializers.SerializerMethodField()
    tier = serializers.SerializerMethodField()

    class Meta:
        model = TaggUser
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "thumbnail_url",
            "biography",
            "profile_pic",
            "header_pic",
            "tier",
        ]

    def get_thumbnail_url(self, user):
        return profile_thumbnail_url(user.id)

    def get_profile_pic(self, user):
        return profile_pic_url(user.id)

    def get_header_pic(self, user):
        return header_pic_url(user.id)

    def get_tier(self, user):
        # TODO: default to tier 1 for now
        return GamificationTier.ONE.value


class WebUserProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    tagg_score = serializers.SerializerMethodField()
    skin = serializers.SerializerMethodField()
    pages = serializers.SerializerMethodField()
    home_widgets = serializers.SerializerMethodField()

    class Meta:
        model = TaggUser
        fields = ["user", "tagg_score", "skin", "pages", "home_widgets"]

    def get_user(self, user):
        return WebUserSerializer(user).data

    def get_tagg_score(self, user):
        game_profile = GameProfile.objects.filter(tagg_user=user).first()
        if game_profile:
            return game_profile.tagg_score
        return 0

    def get_skin(self, user):
        return SkinSerializer(Skin.objects.get(owner=user, active=True)).data

    def get_pages(self, user):
        pages = get_moment_categories(user)
        uid = TaggUser.objects.get(username=user).id
        validPages = []

        for page in pages:
            if page == "__TaggUserHomePage__":
                validPages.insert(0, page)
                # validPages.append(page)
            moments = Moment.objects.filter(user_id=uid, moment_category=page)
            if len(moments) != 0:
                validPages.append(page)
        return validPages

    def get_home_widgets(self, user):
        return WidgetSerializer(
            Widget.objects.filter(owner=user, page=HOMEPAGE, active=True)
            .order_by("order")
            .select_subclasses(),
            many=True,
        ).data


class WebMomentCommentSerializer(serializers.ModelSerializer):
    commenter = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = MomentComments
        fields = ["comment_id", "commenter", "comment", "date_created", "like_count"]

    def get_commenter(self, comment):
        return WebUserSerializer(comment.commenter).data

    def get_like_count(self, comment):
        return CommentsReactionList.objects.filter(
            Q(reaction__reaction_object_id=comment.comment_id)
        ).count()


class WebMomentPostSerializer(serializers.ModelSerializer):
    top_comment = serializers.SerializerMethodField()
    user = serializers.SerializerMethodField()

    class Meta:
        model = Moment
        fields = [
            "moment_id",
            "caption",
            "moment_url",
            "thumbnail_url",
            "moment_category",
            "view_count",
            "share_count",
            "top_comment",
            "user",
        ]

    def get_top_comment(self, moment):
        comments = MomentComments.objects.filter(moment_id=moment)
        if comments:
            top_comment = functools.reduce(
                lambda acc, c: acc if acc.comment_id > c.comment_id else c, comments
            )
            return WebMomentCommentSerializer(top_comment).data
        else:
            return {}

    def get_user(self, moment):
        return WebUserSerializer(moment.user_id).data
