import re

EMAIL_REGEX = re.compile(
    r'^(([^<>()[\]\\.,;:\s@"]+(\.[^<>()[\]\\.,;:\s@"]+)*)|'
    r'(".+"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}])|'
    r"(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
)
PHONE_NUMBER_REGEX = re.compile(r"^((\+1)?[0-9]{10})$")
PASSWORD_REGEX = re.compile(
    r"^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9])(?!.*\s).{8,120}$"
)
USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_.]{3,30}$")
NAME_REGEX = re.compile(r"^(?! )[A-Za-z'\-,. ]{2,20}(?<! )$")
WEBSITE_REGEX = re.compile(
    r"^$|^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,50}\.[a-zA-Z0-9()]{2,6}\b([-a-zA-Z0-9()@:%_\+.~#?&/=]{0,35})$"
)
