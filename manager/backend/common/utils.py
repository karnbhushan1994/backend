import logging
import random

from ..messaging.models import Chat

logger = logging.getLogger(__name__)


class RetrieveChatTokenException(Exception):
    pass


def normalize_phone_number(phone_number):
    """Normalize the given phone number

    Args :
      phone_number (str)

    Returns  :
      normalized_phone_number (str)
    """
    normalized_phone_number = "".join(e for e in phone_number if e.isdigit())
    if len(normalized_phone_number) == 12 and normalized_phone_number.startswith("+1"):
        return normalized_phone_number

    elif len(normalized_phone_number) == 11 and normalized_phone_number.startswith("1"):
        return "+" + normalized_phone_number

    elif len(normalized_phone_number) == 10:
        return "+1" + normalized_phone_number


def create_chat_token(stream_client, user):
    """
    Creates chat token for user, stores it in Chat table and returns it
    """
    try:
        chat_token = stream_client.create_token(str(user.id))
        obj, created = Chat.objects.get_or_create(user=user, chat_token=chat_token)
        return chat_token, created
    except Exception as error:
        Chat.objects.filter(user=user).delete()
        logger.exception(error)
        return None, None


def get_chat_token(stream_client, user):
    """
    Retireves/Creates chat token for user and returns it
    """
    try:
        chat_token = ""
        if Chat.objects.filter(user=user).exists():
            chat_token = Chat.objects.get(user=user).chat_token
            created = True
        else:
            chat_token, created = create_chat_token(stream_client, user)

        return chat_token, created

    except Exception as error:
        logger.exception(error)
        raise RetrieveChatTokenException


def update_stream_user_profile(stream_client, userlist):
    """
    Creates/updates user profiles {id, first_name, last_name, username, thumbnail_url} on Stream
    """
    stream_client.update_users(userlist)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def light_shuffle(l, chunk_size=5, seed=0):
    """
    Performs a "light" shuffle. Using the seed to shuffle each chunk to make
    things seem random.
    """
    out = []
    for chunk in chunks(l, chunk_size):
        shuffled_chunk = chunk
        random.Random(seed).shuffle(shuffled_chunk)
        out += shuffled_chunk
    return out


def permission_by_action(original_class):
    """
    A class decorator for allowing permission classes by action.

    Example:

    @permission_by_action
    class TestViewSet(viewsets.ViewSet):
        permission_classes_by_action = {
            "default": [IsAuthenticated],
            "retrieve": [AllowAny],
        }
        ...
    """
    # https://stackoverflow.com/a/36007881
    def get_permissions(self):
        if "permission_classes_by_action" not in self.__class__.__dict__:
            raise NotImplementedError("Missing field: permission_classes_by_action")
        try:
            # return permission_classes depending on `action`
            return [
                permission()
                for permission in self.permission_classes_by_action[self.action]
            ]
        except KeyError:
            # action is not set return default permission_classes
            return [
                permission()
                for permission in self.permission_classes_by_action["default"]
            ]

    original_class.get_permissions = get_permissions
    return original_class
