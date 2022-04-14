from hashlib import blake2b
from hmac import compare_digest
import secrets


class HashManager:
    """
    Class to generate and verify hashes
    """

    def __init__(self, size, secret):
        self.size = size
        self.secret = secret

    def generate_secret_key(bytes):
        """Can be used to generate secret tokens

        Args:
            Number of bytes needed for the token

        Returns:
            Hexadecimal hash value
        """
        return secrets.token_hex(bytes)

    # The following code has been taken from
    # https://docs.python.org/3/library/hashlib.html
    def sign(self, cookie):
        """Generates a signature for the input string

        Args:
            cookie:(str) String to be hashed

        Returns:
            (bytes) Hashed value of the specified size
        """
        hashed = blake2b(digest_size=self.size, key=self.secret)
        hashed.update(cookie)
        return hashed.hexdigest().encode("utf-8")

    def verify(self, cookie, signature):
        """Verifies the signature for the input string

        Args:
            cookie:(str) String to be hashed
            signature : (bytes) Hashed value

        Returns:
             (bool) True or False depending on whether the provided signature matches the actual signature or not
        """
        correct_signature = self.sign(cookie)
        return compare_digest(correct_signature, signature)
