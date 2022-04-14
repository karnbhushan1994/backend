from rest_framework import serializers

from .models import UserInterests


class UserInterestsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserInterests
        fields = "__all__"
