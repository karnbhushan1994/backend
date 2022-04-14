from rest_framework import serializers

from .models import MomentTag
from ...serializers import TaggUserSerializer


class MomentTagSerializer(serializers.ModelSerializer):
    user = TaggUserSerializer()

    class Meta:
        model = MomentTag
        fields = "__all__"
