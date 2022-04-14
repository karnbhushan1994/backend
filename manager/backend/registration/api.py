import logging

from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..common.constants import HOMEPAGE, SMS_WAITLIST_CONFIRMED
from ..common.sms_manager import send_sms
from ..common.validator import FieldException
from ..models import TaggUser, VIPUser
from ..moments.moment_category.utils import create_single_moment_category
from ..serializers import TaggUserSerializer
from .utils import validate_fields
from ..gamification.models import GameProfile


class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    serializer_class = TaggUserSerializer

    def __init__(self, *args, **kwargs):
        super(RegisterViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        try:
            body = request.POST
            validate_fields(body, check_required_fields=True)

            first_name = body["first_name"]
            last_name = body["last_name"]
            email = body["email"]
            phone_number = body["phone_number"]
            username = body["username"]
            password = body["password"]
            tiktok_handle = ''
            if 'tiktok_handle' in body:
                tiktok_handle = body["tiktok_handle"]
            gender = ''
            if 'gender' in body:
                gender = body["gender"]
            birthday = ''
            if 'birthday' in body:
                birthday = body["birthday"]        
            if not phone_number.startswith("+1"):
                phone_number = "+1" + phone_number
            instagram_handle=tiktok_handle.split('/') 
            user = TaggUser.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number,
                username=username,
                password=password,
                tiktok_handle=tiktok_handle,
                instagram_handle=instagram_handle[3],
                gender=gender,
                birthday=birthday,
            )

            # Create a mandatory home page
            create_single_moment_category(user, HOMEPAGE)

            # Create gamification profile for user
            if not GameProfile.objects.filter(tagg_user=user).exists():
                GameProfile.objects.create(tagg_user=user)

            is_vip = VIPUser.objects.filter(phone_number=phone_number).exists()

            if is_vip:
                user.taggusermeta.is_onboarded = True
            else:
                send_sms(user.phone_number, SMS_WAITLIST_CONFIRMED)

            return Response(
                {
                    "user_id": user.id,
                    "token": Token.objects.get(user=user).key,
                },
                201,
            )
        except FieldException as error:
            self.logger.error(error)
            return Response(str(error), 400)
        except Exception as error:
            self.logger.exception(error)
            return Response("Something went wrong", status=500)

    @action(detail=False, methods=["post"])
    def validate(self, request):
        try:
            body = request.POST
            validate_fields(body, check_required_fields=False)
            return Response("Success! All fields are valid.")
        except FieldException as error:
            self.logger.error(error)
            return Response(str(error), status=400)
        except Exception as error:
            self.logger.exception(error)
            return Response("Something went wrong", status=500)
