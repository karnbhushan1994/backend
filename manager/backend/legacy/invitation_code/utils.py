import random
import string

from ..models import TaggUser
from .models import InvitationCode


class InvitaitonCodeException(Exception):
    pass


def generate_token():
    letters = string.ascii_uppercase
    unique_code = True

    while unique_code:

        generated_token = "".join(random.choice(letters) for _ in range(6))

        if InvitationCode.objects.filter(hexcode=generated_token):
            unique_code = False

        if unique_code == True:
            entry = InvitationCode(hexcode=generated_token)
            entry.save()
            break
        else:
            unique_code = True

    return entry


def is_invitation_code_valid(code):
    """
    An invitation code is valid when it exists in
    the table AND it is unoccupied, meaning it
    doens't have a username on it.
    """
    ics = InvitationCode.objects.filter(hexcode=code)
    if not ics:
        raise InvitaitonCodeException("Code not found")
    ic = ics[0]
    if ic.username:
        raise InvitaitonCodeException("Code already used")
    return ic


def validate_invitation_code_and_onboard(code, username):
    ic = is_invitation_code_valid(code)
    ic.username = username
    users = TaggUser.objects.filter(username=username)
    if not users:
        raise InvitaitonCodeException("User not found")
    user = users[0]
    if user.taggusermeta.is_onboarded:
        raise InvitaitonCodeException("User already onboarded")
    user.taggusermeta.is_onboarded = True
    ic.save()
    user.save()
    return True
