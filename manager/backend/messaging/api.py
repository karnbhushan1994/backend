import logging
from django.conf import settings
from stream_chat.client import StreamChat
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action

from ..common.utils import get_chat_token, update_stream_user_profile
from ..serializers import TaggUserSerializer


class ChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(ChatViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @action(detail=False, methods=["get"])
    def get_token(self, request, pk=None):
        """
        Returns request user's chat token
        """
        try:
            stream_client = StreamChat(
                api_key=settings.STREAM_API_KEY, api_secret=settings.STREAM_API_SECRET
            )
            chat_token, created = get_chat_token(stream_client, request.user)
            update_stream_user_profile(
                stream_client, [TaggUserSerializer(request.user).data]
            )

            chat_token = chat_token if chat_token else ""

            if created:
                return Response({"chatToken": chat_token}, status=200)
            else:
                return Response("Unable to create chat token", status=500)
        except Exception as err:
            logging.exception("Internal Server Error", status=500)
