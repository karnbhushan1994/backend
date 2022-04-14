from rest_framework import serializers

from .models import DiscoverCategory
from ..suggested_people.models import Badge


class DiscoverCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscoverCategory
        fields = "__all__"


class BadgeToDiscoverCategorySerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ["id", "name", "category"]

    def get_id(self, obj):
        # Increment the id so it doesn't conflict with discover category ids
        return obj.id + 100000

    def get_name(self, obj):
        return obj.name

    def get_category(self, obj):
        return "Badge"
