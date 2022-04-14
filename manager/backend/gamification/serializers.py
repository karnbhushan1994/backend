from rest_framework import serializers

from ..serializers import TaggUserSerializer
from .models import GameProfile, Feature, UserFeature


class GameProfileSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = GameProfile
        fields = ["user", "tagg_score", "tier", "rewards", "newRewardsReceived"]

    def get_user(self, obj):
        return TaggUserSerializer(obj.tagg_user).data


class FeatureSerializer(serializers.ModelSerializer):
    unlocked = serializers.BooleanField(default=False)

    class Meta:
        model = Feature
        fields = "__all__"
        extra_fields = ["unlocked"]


class UserFeatureSerializer(serializers.ModelSerializer):
    feature = serializers.SerializerMethodField()

    class Meta:
        model = UserFeature
        fields = "__all__"

    def get_feature(self, user_feature):
        feature = user_feature.feature
        feature.unlocked = True
        return FeatureSerializer(feature).data


class UserFeatureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeature
        fields = ("user", "feature", "active")
