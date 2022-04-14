from ..suggested_people.utils import mark_user_dirty
from ..common.validator import FieldException
import re
from ..models import TaggUser

VALID_IMAGE_KEYS = ["smallProfilePicture", "largeProfilePicture"]
VALID_PROFILE_KEYS = [
    "first_name",
    "last_name",
    "birthday",
    "biography",
    "website",
    "gender",
    "university_class",
    "snapchat",
    "tiktok",
    "suggested_people_linked",
    "university",
]


class IllegalFormException(Exception):
    pass


def update_field(field, user, social):
    """Helper function to pick the updater function based on the field

    Args:
        field (str): field we want to check
        user (TaggUser): the user we're updating
        social (SocialLink): the social link of the user

    Returns:
        func: the update function for the field type

    Raises:
        FieldException: unsupported field
    """
    if field == "first_name":
        return lambda x: user.update(first_name=x)
    if field == "last_name":
        return lambda x: user.update(last_name=x)
    if field == "birthday":
        return lambda x: user.update(birthday=x)
    if field == "biography":
        return lambda x: user.update(biography=x)
    if field == "website":
        return lambda x: user.update(website=x)
    if field == "gender":
        return lambda x: user.update(gender=x)
    if field == "suggested_people_linked":
        mark_user_dirty(str(user[0].id))

        def lambda_x(x):
            user[0].taggusermeta.suggested_people_linked = x
            user[0].save()

        return lambda_x
    if field == "university_class":
        mark_user_dirty(str(user[0].id))
        return lambda x: user.update(university_class=x)
    if field == "snapchat":
        return lambda x: social.update(snapchat_username=x)
    if field == "tiktok":
        return lambda x: social.update(tiktok_username=x)
    if field == "university":
        mark_user_dirty(str(user[0].id))
        return lambda x: user.update(university=x)
    raise FieldException(f"Invalid field: {field}")
