from .models import LoginCount
from rest_framework import serializers


class LoginCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginCount
        fields = ["count"]
