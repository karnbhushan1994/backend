from rest_framework import serializers

from ..models import BlockedUser, TaggUser

from ..gamification.models import GameProfile

import json


class BaseProfileInfoSerializer:
    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_tagg_score(self, obj):
        profile = GameProfile.objects.get(tagg_user=obj.id)
        return profile.tagg_score

    def get_rewards(self, obj):
        profile = GameProfile.objects.get(tagg_user=obj.id)
        return json.loads(profile.rewards)

    def get_newRewardsReceived(self, obj):
        profile = GameProfile.objects.get(tagg_user=obj.id)
        return json.loads(profile.newRewardsReceived)

    def get_birthday(self, obj):
        return obj.birthday

    def get_snapchat(self, obj):
        link = self.context.get("social_link")
        if not link:
            raise Exception("social_link context not initialized")
        return link.snapchat_username

    def get_tiktok(self, obj):
        link = self.context.get("social_link")
        if not link:
            raise Exception("social_link context not initialized")
        return link.tiktok_username

    def get_friendship_status(self, obj):
        friendship_status = self.context.get("friendship_status")
        if not friendship_status:
            raise Exception("friendship_status context not initialized")
        return friendship_status

    def get_friendship_requester_id(self, obj):
        friendship_requester_id = self.context.get("friendship_requester_id")
        if friendship_requester_id == None:
            raise Exception("friendship_requester_id context not initialized")
        return friendship_requester_id

    def get_is_blocked(self, obj):
        # Retrieve is user has been blocked by the requester
        requester_id = self.context.get("requester_id")
        request_user = TaggUser.objects.get(id=requester_id)
        user = TaggUser.objects.get(id=obj.id)

        is_blocked = BlockedUser.objects.filter(
            blocked=user, blocker=request_user
        ).exists()
        return is_blocked


class ProfileInfoSerializer(serializers.ModelSerializer, BaseProfileInfoSerializer):
    name = serializers.SerializerMethodField()
    tagg_score = serializers.SerializerMethodField()
    friendship_status = serializers.SerializerMethodField()
    friendship_requester_id = serializers.SerializerMethodField()
    is_blocked = serializers.SerializerMethodField()

    class Meta:
        model = TaggUser
        fields = [
            "name",
            "username",
            "biography",
            "website",
            "university",
            "university_class",
            "friendship_status",
            "friendship_requester_id",
            "tagg_score",
            "is_blocked",
        ]


class OwnerProfileInfoSerializer(
    serializers.ModelSerializer, BaseProfileInfoSerializer
):
    name = serializers.SerializerMethodField()
    tagg_score = serializers.SerializerMethodField()
    rewards = serializers.SerializerMethodField()
    newRewardsReceived = serializers.SerializerMethodField()
    birthday = serializers.SerializerMethodField()
    snapchat = serializers.SerializerMethodField()
    tiktok = serializers.SerializerMethodField()
    friendship_status = serializers.SerializerMethodField()
    friendship_requester_id = serializers.SerializerMethodField()
    profile_tutorial_stage = serializers.SlugRelatedField(
        source="taggusermeta",
        read_only=True,
        many=False,
        slug_field="profile_tutorial_stage",
    )
    suggested_people_linked = serializers.SlugRelatedField(
        source="taggusermeta",
        read_only=True,
        many=False,
        slug_field="suggested_people_linked",
    )
    is_blocked = serializers.SerializerMethodField()

    class Meta:
        model = TaggUser
        fields = [
            "name",
            "username",
            "biography",
            "website",
            "birthday",
            "gender",
            "university",
            "university_class",
            "profile_tutorial_stage",
            "suggested_people_linked",
            "snapchat",
            "tiktok",
            "friendship_status",
            "friendship_requester_id",
            "tagg_score",
            "is_blocked",
            "rewards",
            "newRewardsReceived",
        ]
