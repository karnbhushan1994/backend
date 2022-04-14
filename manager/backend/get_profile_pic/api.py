import json
import os

import boto3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import FileResponse
from django.http.response import HttpResponse
from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from rest_framework.permissions import IsAuthenticated
import logging
from ..models import TaggUser
from ..serializers import TaggUserSerializer
from ..common.image_manager import profile_pic_url, header_pic_url


class ProfilePicViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(ProfilePicViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk=None):
        try:
            return Response({"url": profile_pic_url(pk)})
        except Exception as error:
            self.logger.exception(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class HeaderPicViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(HeaderPicViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk=None):
        try:
            return Response({"url": header_pic_url(pk)})
        except Exception as error:
            self.logger.exception(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
