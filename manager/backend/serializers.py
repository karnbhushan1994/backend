from rest_framework import serializers

from .common.image_manager import profile_thumbnail_url
from .friends.models import Friends
from .models import InviteFriends, TaggUser


class TaggUserSerializer(serializers.ModelSerializer):
    thumbnail_url = serializers.SerializerMethodField()

    class Meta:
        model = TaggUser
        fields = ["id", "username", "first_name", "last_name", "thumbnail_url"]

    def get_thumbnail_url(self, obj):
        return profile_thumbnail_url(obj.id)


class FriendsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = ["requested"]


class InviteFriendsSerializer(serializers.ModelSerializer):
    phoneNumber = serializers.CharField(source="invitee_phone_number")
    firstName = serializers.CharField(source="invitee_first_name")
    lastName = serializers.CharField(source="invitee_last_name")

    class Meta:
        model = InviteFriends
        fields = ("phoneNumber", "firstName", "lastName")
