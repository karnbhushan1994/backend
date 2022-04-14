import logging
from rest_framework import viewsets
import json
from ..common.validator import get_response, check_is_valid_parameter
from ..models import WaitlistUser, TaggUser
from rest_framework.permissions import AllowAny
from django.db import IntegrityError


class WaitlistUserViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super(WaitlistUserViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, pk=None):
        """
        Add user to wait list
        Do not add users who are either already on the app or on the wait list
        """
        try:
            body = json.loads(request.body)
            if not check_is_valid_parameter("phone_number", body):
                return get_response("phone_number is required", type=400)
            if not check_is_valid_parameter("first_name", body):
                return get_response("first_name is required", type=400)
            if not check_is_valid_parameter("last_name", body):
                return get_response("last_name is required", type=400)
            phone_number = body["phone_number"]
            first_name = body["first_name"]
            last_name = body["last_name"]
            if TaggUser.objects.filter(phone_number=phone_number).exists():
                return get_response("The user is already registered with us", type=409)
            if not phone_number.startswith("+1"):
                phone_number = "+1" + phone_number
            waitlist_user = WaitlistUser.objects.create(
                phone_number=phone_number, first_name=first_name, last_name=last_name
            )
            waitlist_user.save()
            return get_response("Success", type=200)
        except UnicodeDecodeError:
            self.logger.exception("Expected JSON data in request body.")
            return get_response("Expected JSON data in request body.", type=400)
        except json.decoder.JSONDecodeError:
            self.logger.exception("Expected JSON-formatted data.")
            return get_response("Expected JSON-formatted data.", type=400)
        except IntegrityError:
            self.logger.error("The user is already in the waitlist")
            return get_response("The user is already in the waitlist", type=409)
        except Exception as err:
            self.logger.exception(
                "Some problem occured while creating the user for waitlist."
            )
            return get_response(
                "Some problem occured while creating the user for waitlist.", type=500
            )
