import time
import logging
from django_otp.oath import TOTP


class TokenManager:
    def __init__(self):
        # counter with which last token was verified.
        # Next token must be generated at a higher counter value.
        self.last_verified_counter = -1
        # this value will return True, if a token has been successfully
        # verified.
        self.verified = False
        # number of digits in a token. Default is 6
        self.number_of_digits = 4
        # validity period of a token. Default is 30 second.
        self.token_validity_period = 120
        self.logger = logging.getLogger(__name__)

    def totp_obj(self, key_value):
        # creating a TOTP object
        key_value = key_value
        totp = TOTP(
            key=key_value, step=self.token_validity_period, digits=self.number_of_digits
        )
        totp.time = time.time()
        return totp

    def generate_token(self, key_value):
        # get the TOTP object and use that to create token
        totp = self.totp_obj(key_value)
        # token can be obtained with `totp.token()`
        token = str(totp.token()).zfill(4)
        return token

    def verify_token(self, key_value, token, tolerance=1):
        try:
            # convert the input token to integer
            token = int(token)
        except ValueError:
            self.logger.exception("Value Error")
            # return False, if token could not be converted to an integer
            self.verified = False
        else:
            totp = self.totp_obj(key_value)
            # check if the current counter value is higher than the value of
            # last verified counter and check if entered token is correct by
            # calling totp.verify_token()
            if (totp.t() > self.last_verified_counter) and (
                totp.verify(token, tolerance=tolerance)
            ):
                # if the condition is true, set the last verified counter value
                # to current counter value, and return True
                self.last_verified_counter = totp.t()
                self.verified = True
            else:
                # if the token entered was invalid or if the counter value
                # was less than last verified counter, then return False
                self.verified = False
        return self.verified
