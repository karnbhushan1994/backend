import logging
from ..profile.utils import get_profile_info_serialized

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..common.validator import get_response
from ..serializers import TaggUserSerializer


class UserProfileInfoViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(UserProfileInfoViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk=None):
        """Handles a GET request to this endpoint (with pk)."""
        try:
            serialized = get_profile_info_serialized(request.user, pk)
            return Response(serialized)
        except Exception as error:
            self.logger.exception(error)
            return get_response("Request failed with unknown reason", type=500)

    serializer_class = TaggUserSerializer
