import random

from django.core.cache import cache
from rest_framework import serializers

from ..models import TaggUser
from ..serializers import TaggUserSerializer
from ..social_linking.utils import get_linked_socials
from .models import Badge
from .utils import (
    fetch_suggested_people_url,
    get_badges_for_user,
    get_friendship,
    get_mutual_friends,
)


class BadgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Badge
        fields = "__all__"


class SuggestedPeopleSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    mutual_friends = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    social_links = serializers.SerializerMethodField()
    suggested_people_url = serializers.SerializerMethodField()
    friendship = serializers.SerializerMethodField()
    university = serializers.SerializerMethodField()

    class Meta:
        model = TaggUser
        fields = [
            "user",
            "mutual_friends",
            "badges",
            "social_links",
            "suggested_people_url",
            "friendship",
            "university",
        ]

    def get_user(self, obj):
        return TaggUserSerializer(obj).data

    def get_mutual_friends(self, obj):
        request_user = self.context.get("user")
        cache_time = 60 ** 3
        cache_key = f"friendship_{request_user.id}_{obj.id}"
        mutual_friends = cache.get(cache_key)

        if mutual_friends == None:
            mutual_friends = get_mutual_friends(request_user, obj, shuffled=False)
            cache.set(cache_key, mutual_friends, cache_time)

        random.shuffle(mutual_friends)

        return TaggUserSerializer(mutual_friends, many=True).data

    def get_badges(self, obj):
        return BadgeSerializer(get_badges_for_user(obj), many=True).data

    def get_social_links(self, obj):
        return get_linked_socials(obj)

    def get_suggested_people_url(self, obj):
        return fetch_suggested_people_url(obj)

    def get_friendship(self, obj):
        return get_friendship(self.context.get("user"), obj)

    def get_university(self, obj):
        return obj.university
