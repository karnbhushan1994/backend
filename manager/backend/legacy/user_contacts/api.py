import json
import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..common.constants import INVITE_FRIEND_LIMIT
from ..common.utils import normalize_phone_number
from ..models import InviteFriends, TaggUser
from ..serializers import InviteFriendsSerializer
from .utils import invites_left


class UserContactsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(UserContactsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @action(detail=False, methods=["post"])
    def find_friends(self, request):
        try:
            user = request.user
            body = json.loads(request.body)
            if "contacts" not in body:
                return Response(
                    "contacts is required", status=status.HTTP_400_BAD_REQUEST
                )

            """
            Normalizing phone numbers in contacts to find unregistered contacts
            and creating an array of normalized phone numbers received to find registered users
            """
            phone_numbers = []
            contacts = body["contacts"]

            for contact in contacts:
                normalized_number = normalize_phone_number(contact["phone_number"])

                if normalized_number:
                    phone_numbers.append(normalized_number)
                    contact["phone_number"] = normalized_number
                else:
                    contact["phone_number"] = None

            # Creating a list of non tagg users who did not receive an invite yet
            existing_phone_number = set([])

            # populate the lookup table first
            existing_phone_number.update(
                [
                    x["phone_number"]
                    for x in TaggUser.objects.all().values("phone_number")
                ]
            )
            existing_phone_number.update(
                [
                    x["invitee_phone_number"]
                    for x in InviteFriends.objects.all().values("invitee_phone_number")
                ]
            )

            seen = set()
            unregistered_contacts = []
            for contact in contacts:
                if (
                    contact["phone_number"]
                    and contact["phone_number"] not in existing_phone_number
                    and contact["phone_number"] not in seen
                ):
                    unregistered_contacts.append(
                        {
                            "phoneNumber": contact["phone_number"],
                            "firstName": contact["first_name"],
                            "lastName": contact["last_name"],
                        }
                    )
                    seen.add(contact["phone_number"])

            pending_users = InviteFriends.objects.filter(inviter=user)

            return Response(
                {
                    "invite_from_contacts": unregistered_contacts,
                    "pending_users": InviteFriendsSerializer(
                        pending_users, many=True
                    ).data,
                }
            )
        except Exception as err:
            self.logger.exception(err)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["post"])
    def invite_friend(self, request):
        try:
            user = request.user
            body = json.loads(request.body)
            if "invitee_phone_number" not in body:
                return Response(
                    "invitee_phone_number is required",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if "invitee_first_name" not in body:
                return Response(
                    "invitee_first_name is required", status=status.HTTP_400_BAD_REQUEST
                )
            if "invitee_last_name" not in body:
                return Response(
                    "invitee_last_name is required", status=status.HTTP_400_BAD_REQUEST
                )
            if "reminding" not in body:
                return Response(
                    "reminding is required", status=status.HTTP_400_BAD_REQUEST
                )
            if not body["reminding"] and invites_left(user) < 1:
                return Response(
                    f"Exceeded number of invite limit ({INVITE_FRIEND_LIMIT})", 400
                )

            invited, created = InviteFriends.objects.get_or_create(
                invitee_phone_number=body["invitee_phone_number"],
                defaults={
                    "invitee_first_name": body["invitee_first_name"],
                    "invitee_last_name": body["invitee_last_name"],
                    "inviter_fullname": f"{user.first_name} {user.last_name}",
                    "inviter": user,
                    "invited": True,
                    "invite_code": generate_token(),
                },
            )
            code = invited.invite_code
            if not created and not code:
                code = generate_token()
                invited.invite_code = code
                invited.save()

            return Response(
                {
                    "invite_code": code.hexcode,
                },
                201 if created else 200,
            )
        except Exception as err:
            self.logger.exception(err)
            return Response(
                "Internal server error", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def check_invite_count(self, request):
        try:
            return Response({"invites_left": invites_left(request.user)})
        except Exception as err:
            self.logger.exception(err)
            return Response("Something went wrong", 500)
