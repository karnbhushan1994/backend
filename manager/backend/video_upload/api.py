import datetime
import json
import logging
import os

from django.conf import settings
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..common.validator import check_is_valid_parameter, get_response
from ..models import TaggUser
from ..moments.models import Moment
from .utils import create_presigned_post


class PresignedURLViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(PresignedURLViewset, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """Generate Presigned URL to send to client
            URL : /api/presigned-url/create/

         Args:
            filename - this is something we should generate ourselves either in the frotnend or the backend
            should be a unique identifier like a hash or someth
            We will want to have a more sophisticated organizational system for how we manage uploads
            We should handle bucket/object naming schemes and every other 'create_presigned_post' param

        Returns:
            A URL
            A status code
        """
        # verifying the payload is valid - username or email. - we can just get this from async storage
        try:
            body = json.loads(request.body)
            if not check_is_valid_parameter("filename", body):
                self.logger.error("filename is required")
                return get_response(data="filename is required", type=400)

            filename = body["filename"]

            # want to generate presigned URL here and return it, if possible.
            upload_url = create_presigned_post(filename)
            if upload_url:
                # the response we return will give us the URL the client will use to make the POST request to, and a set of x-amz fields to use as credentials
                return Response(
                    {
                        "response_msg": "Success: Generated a url",
                        "response_url": upload_url,
                    }
                )
            else:
                return get_response(data="Problem generating presigned url", type=500)
        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user Id.")
            return get_response(data="Invalid user ID.", type=404)
        except Exception as err:
            self.logger.exception("Problem generating presigned url")
            self.logger.exception(err)
            return get_response(data="Problem generating presigned url", type=500)
