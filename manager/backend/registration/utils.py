from ..common.validator import FieldException, validate_field

required_fields = [
    "first_name",
    "last_name",
    "email",
    "phone_number",
    "username",
    "password",
    #"tiktok_handle",
]


def validate_fields(body, check_required_fields):
    """Helper function to validate fields of a request body.

    Args:
        body (dict): request body
        check_required_fields (bool): if should check all required fields are
            present.

    Returns:
        None

    Raises:
        FieldException: Any kinds of invalid/missing fields
    """
    for field in required_fields:
        if check_required_fields and field not in body:
            raise FieldException(f"{field} is required")
        if not check_required_fields and field not in body:
            continue
        validate_field(field)(body[field])
