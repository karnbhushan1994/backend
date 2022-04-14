import logging
from enum import Enum

from django.core.exceptions import ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..skins.utils import create_default_skin

from ..common.otp_manager import OtpType, send_otp, verify_otp
from ..common.regex import PHONE_NUMBER_REGEX
from ..models import TaggUser, VIPUser
from ..serializers import TaggUserSerializer
from ..user_interests.models import UserInterests
from ..skins.models import Skin


class PhoneStatus(Enum):
    AVAILABLE = "AVAILABLE"
    REGISTERED = "REGISTERED"
    ON_WAITLIST = "ON_WAITLIST"
    INVALID_FORMAT = "INVALID_FORMAT"


class PhoneViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @action(detail=False, methods=["post"])
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["phone_number"],
            properties={"phone_number": openapi.Schema(type=openapi.TYPE_STRING)},
        )
    )
    def status(self, request):
        if "phone_number" not in request.data:
            raise ValidationError({"phone_number": "This field is required"})

        phone = request.data["phone_number"]

        if not PHONE_NUMBER_REGEX.match(phone):
            return Response(PhoneStatus.INVALID_FORMAT.name)

        users = TaggUser.objects.filter(phone_number=phone)

        if not users:
            return Response(PhoneStatus.AVAILABLE.name)

        user = users[0]

        if user.taggusermeta.is_onboarded:
            return Response(PhoneStatus.REGISTERED.name)
        else:
            return Response(PhoneStatus.ON_WAITLIST.name)


class SendOtpViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super(SendOtpViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        try:
            if "phone_number" not in request.data:
                raise ValidationError({"phone_number": "This field is required."})

            phone_number = request.data.get("phone_number")

            if not send_otp(phone_number, OtpType.ACCOUNT_ACTIVATION):
                return Response(
                    "There was a problem while sending the verification code", 500
                )

            return Response("success")

        except Exception as err:
            self.logger.exception(
                "There was a problem while sending the verification code"
            )
            return Response(
                "There was a problem while sending the verification code", 500
            )

    serializer_class = TaggUserSerializer


class VerifyOtpViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = TaggUserSerializer

    def __init__(self, *args, **kwargs):
        super(VerifyOtpViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        try:
            for key in ["phone_number", "otp"]:
                if key not in request.data:
                    return Response({key: "This field is required."}, 400)

            phone_number = request.data.get("phone_number")
            otp = request.data.get("otp")

            if not verify_otp(phone_number, otp):
                return Response("Invalid OTP", 401)

            users = TaggUser.objects.filter(phone_number=phone_number)
            is_vip = VIPUser.objects.filter(phone_number=phone_number).exists()

            # if not found, user is just verifying their phone number
            if not users:
                return Response(
                    {
                        "is_vip": is_vip,
                    }
                )
            user = users[0]
            token = Token.objects.get(user=user)
            has_interests = UserInterests.objects.filter(user=user)
            has_profile_template = Skin.objects.filter(owner=user)
            create_default_skin(user)
            return Response(
                {
                    "user_id": user.id,
                    "token": token.key,
                    "username": user.username,
                    "is_vip": is_vip,
                    "is_onboarded": user.taggusermeta.is_onboarded,
                    "is_profile_onboarded": len(has_interests) > 0
                    and len(has_profile_template) > 0,
                    "profile_tutorial_stage": user.taggusermeta.profile_tutorial_stage,
                }
            )
        except Exception:
            self.logger.exception("There was a problem while verifying the OTP")
            return Response("Something went wrong", 500)
