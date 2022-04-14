from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class TestUserRegisteration(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user1 = User.objects.create_user(
            username="tagguser",
            password="taggPassword!123",
            first_name="tagg",
            last_name="user",
            email="tagg@gmail.com",
        )
        self.token1 = Token.objects.get(user=self.user1)

        self.registration_url = "/api/register/"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_registeration(self):
        data = {
            "first_name": "User",
            "last_name": "One",
            "password": "Password!123",
            "username": "user1",
            "email": "user1@email.com",
        }

        # Case 1: No Authorization credentials passed
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertTrue(
            self.client.post(
                self.registration_url, data=data, format="json"
            ).status_code,
            201,
        )

        data = {
            "first_name": "User",
            "last_name": "Two",
            "password": "Password!123",
            "username": "user2",
            "email": "user2@email.com",
        }

        # Case 2: Credientials passed
        self.client.credentials(HTTP_AUTHORIZATION="Token randomstring123")
        self.assertEqual(
            self.client.post(
                self.registration_url, data=data, format="json"
            ).status_code,
            401,
        )
