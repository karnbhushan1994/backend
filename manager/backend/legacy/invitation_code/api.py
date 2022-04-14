import logging

from django.core.exceptions import ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..common.notification_manager import handle_notification
from ..common.validator import check_is_valid_parameter, get_response
from ..models import InvitationCode, InviteFriends, TaggUser
from .utils import (
    InvitaitonCodeException,
    generate_token,
    is_invitation_code_valid,
    validate_invitation_code_and_onboard,
)


class InvitationCodeViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["code"],
            properties={"code": openapi.Schema(type=openapi.TYPE_STRING)},
        )
    )
    @action(detail=False, methods=["post"])
    def verify(self, request):
        try:
            if "code" not in request.data:
                raise ValidationError({"code": "This field is required."})
            if is_invitation_code_valid(request.data["code"]):
                return Response("Valid")
            else:
                return Response("Invalid", 400)
        except InvitaitonCodeException as e:
            self.logger.error(e)
            return Response(str(e), 400)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["code", "username"],
            properties={
                "code": openapi.Schema(type=openapi.TYPE_STRING),
                "username": openapi.Schema(type=openapi.TYPE_STRING),
            },
        )
    )
    @action(detail=False, methods=["post"])
    def onboard(self, request):
        try:
            if "code" not in request.data:
                raise ValidationError({"code": "This field is required."})
            if "username" not in request.data:
                raise ValidationError({"username": "This field is required."})
            code = request.data["code"]
            username = request.data["username"]
            validate_invitation_code_and_onboard(code, username)
            return Response("Success and onboarded")
        except InvitaitonCodeException as e:
            self.logger.error(e)
            return Response(str(e), 400)


class CreateInvitationCode(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super(CreateInvitationCode, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        try:
            token = generate_token()

            data = {}
            data["code"] = token.hexcode
            data["message"] = "Created Invitation Code"

            return Response(data, status=status.HTTP_200_OK)

        except:
            self.logger.exception("Failure creating an invitation code")
            return Response(
                "Failure creating an invitation code",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class VerifyInvitationCode(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super(VerifyInvitationCode, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def destroy(self, request, pk=None):
        data = request.query_params
        if not check_is_valid_parameter("user_id", data):
            return get_response("User id is required", type=400)
        user_id = data.get("user_id")
        try:
            if InvitationCode.objects.get(hexcode=pk):
                InvitationCode.objects.filter(hexcode=pk).delete()
                user = TaggUser.objects.filter(id=user_id).first()
                user.taggusermeta.is_onboarded = True
                user.save()
                # Since user has just onboarded, find inviter from invite friends table to send notification
                invite = InviteFriends.objects.filter(
                    invitee_phone_number=user.phone_number
                ).first()

                if invite:
                    handle_notification(
                        notification_type="INVT_ONBRD",
                        actor=user,
                        receiver=invite.inviter,
                        verbage="Your friend @" + user.username + " has joined tagg!",
                    )

                return Response("Code Verified and Deleted", status=status.HTTP_200_OK)

        except:
            self.logger.exception("Failure verifying the invitation code")
            return Response(
                "Failure verifying the invitation code",
                status=status.HTTP_400_BAD_REQUEST,
            )
