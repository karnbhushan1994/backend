import json
import logging

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated

from .serializers import UserInterestsSerializer


class UserInterestsViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UserInterestsSerializer
    pagination_class = LimitOffsetPagination
    http_method_names = ["post"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        if "interests" not in request.data:
            raise ValidationError({"interests": "This field is required."})
        request.data["user"] = request.user.id
        # storing interests as a serialized json array
        request.data["interests"] = json.dumps(request.data.get("interests"))
        return super().create(request, *args, **kwargs)
