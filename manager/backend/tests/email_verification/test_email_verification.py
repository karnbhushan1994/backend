from rest_framework.test import APIClient, APITestCase
from unittest.mock import patch
from .mocks import TOTPMock, EmailMessageMock
from django.contrib.auth import get_user_model


class EmailVerificationTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tagg",
            password="taggPassword!123",
            first_name="tagg",
            last_name="tagg",
            email="tagg@gmail.com",
        )
        self.send_otp = "/api/send-otp/"
        self.verify_otp = "/api/verify-otp/"
        self.dummy_email = "someone@gmail.com"
        self.dummy_registered_email = "tagg@gmail.com"
        self.dummy_otp = "123456"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    # Testing  : /api/send-otp/
    def test_send_otp_blank_email(self):
        data = {}
        response = self.client.post(self.send_otp, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual("Email is required", response.data)

    def test_send_otp_user_already_exits(self):
        data = {"email": self.dummy_registered_email}
        response = self.client.post(self.send_otp, data, format="json")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            "This email is already registered with us, please use another email.",
            response.data,
        )

    def test_send_otp_email_internal_server_error(self):
        # Sending faulty data
        data = {"email", self.dummy_email}
        response = self.client.post(self.send_otp, data, format="json")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            "There was a problem while sending the verification code", response.data
        )

    @patch("backend.common.token_manager.TOTP", TOTPMock)
    @patch("backend.email_verification.api.EmailMessage", EmailMessageMock)
    def test_send_otp_email_pass(self):
        data = {"email": self.dummy_email}
        response = self.client.post(self.send_otp, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            "Success: One time password is sent to the specified email address",
            response.data,
        )

    # Testing  : /api/verify-otp/
    def test_verify_otp_blank_email_and_otp(self):
        data = {}
        response = self.client.post(self.verify_otp, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual("Email is required", response.data)

    def test_verify_otp_blank_otp(self):
        data = {"email": self.dummy_email}
        response = self.client.post(self.verify_otp, data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual("OTP is required", response.data)

    @patch("backend.common.token_manager.TOTP", TOTPMock)
    def test_verify_otp_wrong_otp(self):
        data = {"email": self.dummy_email, "otp": "234567"}
        response = self.client.post(self.verify_otp, data, format="json")
        self.assertEqual(response.status_code, 401)
        self.assertEqual("Failure: Please enter a valid OTP", response.data)

    def test_verify_otp_internal_server_error(self):
        # Sending faulty data
        data = {"email": 123, "otp": self.dummy_otp}
        response = self.client.post(self.verify_otp, data, format="json")
        self.assertEqual(response.status_code, 500)
        self.assertEqual("There was a problem while verifying the OTP", response.data)

    @patch("backend.common.token_manager.TOTP", TOTPMock)
    def test_verify_otp_success(self):
        data = {"email": self.dummy_email, "otp": self.dummy_otp}
        response = self.client.post(self.verify_otp, data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            "Success: Your email address is successfully verified", response.data
        )
