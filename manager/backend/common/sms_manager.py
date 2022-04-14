from .token_manager import TokenManager
from django.conf import settings
from twilio.rest import Client


def send_sms(phone_number, message_body):
    """Send OTP to the requested phone number

    Args :
      phone_number (str): Phone number of the user
      message_body (str) : Message to be sent

    Returns  :
      bool : True or False
    """
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    message = client.messages.create(
        to=phone_number, from_=settings.TWILIO_PHONE_NUMBER, body=message_body
    )
    return True if message else False
