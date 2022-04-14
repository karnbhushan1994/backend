from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class UserValidateOtp(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tagg_123",
            password="taggPassword!123",
            first_name="tagg",
            last_name="tagg",
            email="tagg@gmail.com",
        )
        self.generate_urls = "/api/password-send-otp/"
        self.validate_urls = "/api/password-verify-otp/"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_generate_otp(self):
        res = self.client.post(
            self.generate_urls, data={"value": "tagg_123"}, format="json"
        )
        res1 = self.client.post(
            self.generate_urls, data={"value": "tagg_1234"}, format="json"
        )
        res2 = self.client.post(self.generate_urls, data={"value": ""}, format="json")
        res3 = self.client.post(
            self.generate_urls, data={"value": "tagg@gmail.com"}, format="json"
        )
        res4 = self.client.post(
            self.generate_urls, data={"value": "tagg123@gmail.com"}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res1.status_code, 404)
        self.assertEqual(res2.status_code, 400)
        self.assertEqual(res3.status_code, 200)
        self.assertEqual(res4.status_code, 404)

    def test_validate_otp(self):
        res = self.client.post(
            self.validate_urls,
            data={
                "username": "tagg_123",
                "password": "taggPassword!123",
                "otp": "13456",
            },
            format="json",
        )
        self.assertEqual(res.status_code, 400)
