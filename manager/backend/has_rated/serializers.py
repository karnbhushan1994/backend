from .models import HasRated
from rest_framework import serializers


class HasRatedSerializer(serializers.ModelSerializer):
    class Meta:
        model = HasRated
        fields = ["hasRated"]
