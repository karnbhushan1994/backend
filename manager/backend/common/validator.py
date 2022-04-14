import logging
from datetime import date

from dateutil.relativedelta import relativedelta
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response

from ..common.constants import BIO_MAX_LENGTH, GENDER_MAX_LENGTH
from ..common.regex import (
    EMAIL_REGEX,
    NAME_REGEX,
    PASSWORD_REGEX,
    PHONE_NUMBER_REGEX,
    USERNAME_REGEX,
    WEBSITE_REGEX,
)
from ..models import TaggUser

logger = logging.getLogger(__name__)

status_map = {
    200: status.HTTP_200_OK,
    201: status.HTTP_201_CREATED,
    204: status.HTTP_204_NO_CONTENT,
    400: status.HTTP_400_BAD_REQUEST,
    401: status.HTTP_401_UNAUTHORIZED,
    403: status.HTTP_403_FORBIDDEN,
    404: status.HTTP_404_NOT_FOUND,
    405: status.HTTP_405_METHOD_NOT_ALLOWED,
    406: status.HTTP_406_NOT_ACCEPTABLE,
    409: status.HTTP_409_CONFLICT,
    500: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


def check_is_valid_parameter(parameter, body):
    """Check if a request parameter is valid or not

    Args :
      parameter (str): Parameter to validate
      body (dict) : Request body

    Returns  :
      bool : True or False
    """
    is_valid = parameter in body and len(body[parameter]) != 0
    if not is_valid:
        logging.error("The required parameter was not found in the request body")
    return is_valid


def get_response(data, **kwargs):
    """Given a response type, get the response object

    Args :
      message (str): Pass empty if nothing is required
      status (int) : A http status

    Returns :
     Response object
    """
    return Response(data, status=status_map[kwargs["type"]])


def is_firstname_valid(data):
    if not NAME_REGEX.match(data):
        raise FieldException("Invalid firstname")
    return True


def is_lastname_valid(data):
    if not NAME_REGEX.match(data):
        raise FieldException("Invalid lastname")
    return True


def is_email_valid(data):
    if not EMAIL_REGEX.match(data):
        raise FieldException("Invalid email")
    if TaggUser.objects.filter(email=data).exists():
        raise FieldException("Email already exists")
    return True


def is_phone_number_valid(data):
    if not PHONE_NUMBER_REGEX.match(data):
        raise FieldException("Invalid phone number")
    if TaggUser.objects.filter(phone_number=data).exists():
        raise FieldException("Phone number already exists")
    if TaggUser.objects.filter(phone_number="+1" + data).exists():
        raise FieldException("Phone number already exists")
    return True


def is_username_valid(data):
    if not USERNAME_REGEX.match(data):
        raise FieldException("Invalid username")
    if TaggUser.objects.filter(username=data).exists():
        raise FieldException("Username already exists")
    return True


def is_password_valid(data):
    if not PASSWORD_REGEX.match(data):
        raise FieldException("Invalid password")
    return True


def is_birthday_valid(data, min_age=13):
    dob = parse_date(data)
    if not dob:
        raise FieldException("Invalid birthday format")
    today = date.today()
    if dob > today - relativedelta(years=min_age):
        raise FieldException(f"User is not at least {min_age} years old")
    return True


def is_website_valid(data):
    if not WEBSITE_REGEX.match(data):
        raise FieldException("Invalid website")
    return True


def is_biography_valid(data):
    if len(data) > BIO_MAX_LENGTH:
        raise FieldException(
            f"Biography must be no longer than {BIO_MAX_LENGTH} characters"
        )
    return True


def is_gender_valid(data):
    if len(data) > GENDER_MAX_LENGTH:
        raise FieldException(
            f"Gender must be no longer than {GENDER_MAX_LENGTH} characters"
        )
    return True


def is_university_valid(data):
    return data in TaggUser.SCHOOLS


def validate_field(field):
    """Helper function to pick the validator function based on the field

    Args:
        field (str): field we want to check

    Returns:
        func: the validator function for the field type

    Raises:
        FieldException: unsupported field
    """
    if field == "first_name":
        return is_firstname_valid
    if field == "last_name":
        return is_lastname_valid
    if field == "email":
        return is_email_valid
    if field == "phone_number":
        return is_phone_number_valid
    if field == "username":
        return is_username_valid
    if field == "password":
        return is_password_valid
    if field == "birthday":
        return is_birthday_valid
    if field == "website":
        return is_website_valid
    if field == "biography":
        return is_biography_valid
    if field == "gender":
        return is_gender_valid
    if field == "tiktok_handle":
        return is_website_valid    
    if field in [
        "suggested_people_linked",
        "university_class",
        "snapchat",
        "tiktok",
    ]:
        return lambda _: True
    # TODO: change to University.UNIVERSITY_CHOICES after adding that model.
    if field == "university":
        return is_university_valid
    raise FieldException(f"Invalid field: {field}")


class FieldException(Exception):
    pass
