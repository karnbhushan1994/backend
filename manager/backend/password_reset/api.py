import json
from django.contrib.auth.hashers import check_password
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
import logging
from ..common.otp_manager import OtpType, send_otp, verify_otp
from ..models import TaggUser
from ..serializers import TaggUserSerializer
from ..common.validator import get_response, check_is_valid_parameter, is_password_valid
from rest_framework.decorators import action


class PasswordResetViewset(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super(PasswordResetViewset, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @action(detail=False, methods=["post"])
    def request(self, request):
        """Send an OTP to the requested user's phone number
            URL : /api/password-reset/request/

         Args:
            value (str): Username / email of the user requesting change of password

        Returns:
            A status code
        """
        try:
            body = json.loads(request.body)
            if not check_is_valid_parameter("value", body):
                self.logger.error("Username/Email is required")
                return get_response(data="Username/Email is required", type=400)
            value = body["value"]
            if TaggUser.objects.filter(username=value).exists():
                user = TaggUser.objects.get(username=value)
            elif TaggUser.objects.filter(email=value).exists():
                user = TaggUser.objects.get(email=value)
            else:
                self.logger.error(
                    "Please enter username/email associated with the Tagg account"
                )
                return get_response(
                    data="Please enter email or username associated with the Tagg account",
                    type=404,
                )
            if send_otp(user.phone_number, OtpType.PASSWORD_RESET):
                return get_response(
                    data="Success: One time password is sent to the specified phone number",
                    type=200,
                )
            else:
                return get_response(data="Problem sending message", type=500)
        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user Id.")
            return get_response(data="Invalid user ID.", type=404)
        except Exception as err:
            self.logger.exception("Problem sending message")
            return get_response(data="Problem sending message", type=500)

    @action(detail=False, methods=["post"])
    def verify(self, request):
        """Reset user's password
            URL : /api/password-reset/verify/

         Args:
            value (str): Username / email of the user requesting change of password
            otp (str): code to be verified against

        Returns:
            A status code
        """
        try:
            body = json.loads(request.body)
            if not check_is_valid_parameter("value", body):
                self.logger.error("Username/Email is required")
                return get_response(data="Username/Email is required", type=400)
            if not check_is_valid_parameter("otp", body):
                self.logger.error("Username/Email is required")
                return get_response(data="otp is required", type=400)
            value = body["value"]
            otp = body["otp"]

            if TaggUser.objects.filter(username=value).exists():
                user = TaggUser.objects.get(username=value)
            elif TaggUser.objects.filter(email=value).exists():
                user = TaggUser.objects.get(email=value)
            else:
                self.logger.error(
                    "Please enter username/email associated with the Tagg account"
                )
                return get_response(
                    data="Please enter username/email associated with the Tagg account",
                    type=404,
                )
            if verify_otp(user.phone_number, otp):
                return get_response(data="Success: Otp verified", type=200)
            else:
                self.logger.error("Failure: Please enter a valid OTP")
                return get_response(data="Failure: Please enter a valid OTP", type=401)
        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user ID.")
            return get_response(data="Invalid user ID.", type=404)
        except Exception:
            self.logger.exception("Problem verifying otp")
            return get_response(data="Problem verifying otp", type=500)

    @action(detail=False, methods=["post"])
    def reset(self, request):
        """Reset user's password
            URL : /api/password-reset/reset/

         Args:
            value (str): Username / email of the user requesting change of password
            password (str): New password

        Returns:
            A status code
        """
        try:
            body = json.loads(request.body)
            if not check_is_valid_parameter("value", body):
                self.logger.error("Username/Email is required")
                return get_response(data="Username/Email is required", type=400)
            if not check_is_valid_parameter("password", body):
                self.logger.error("password is required")
                return get_response(data="Password is required", type=400)
            value = body["value"]
            password = body["password"]
            errors_password = is_password_valid(password)

            if not errors_password:
                self.logger.error(errors_password)
                return get_response(data=errors_password, type=400)
            if TaggUser.objects.filter(username=value).exists():
                user = TaggUser.objects.get(username=value)
            elif TaggUser.objects.filter(email=value).exists():
                user = TaggUser.objects.get(email=value)
            else:
                self.logger.error(
                    "Please enter username/email associated with the Tagg account"
                )
                return get_response(
                    data="Please enter username/email associated with the Tagg account",
                    type=404,
                )
            if check_password(password, user.password_log):
                self.logger.error(
                    "Failure: Please enter a password different from an old one"
                )
                return get_response(
                    data="Failure: Please enter a password different from an old one",
                    type=406,
                )

            user.set_password(password)
            user.password_log = user.password
            user.save()
            return get_response(data="Success: Password updated", type=200)
        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user ID.")
            return get_response(data="Invalid user ID.", type=404)
        except Exception:
            self.logger.exception("Problem changing password")
            return get_response(data="Problem changing password", type=500)

    serializer_class = TaggUserSerializer
