from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class TestUserLogin(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tagguser",
            password="taggPassword!123",
            first_name="tagg",
            last_name="user",
            email="tagg@gmail.com",
        )
        self.token = Token.objects.get(user=self.user)

        self.login_url = "/api/login/"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_login(self):
        data = {"username": self.user.username, "password": self.user.password}

        # Case 1: No Authorization credentials passed
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertTrue(
            self.client.post(self.login_url, data=data, format="json").status_code, 200
        )

        # Case 2: Random Credientials passed
        self.client.credentials(HTTP_AUTHORIZATION="Token randomstring123")
        self.assertEqual(
            self.client.post(self.login_url, data=data, format="json").status_code, 401
        )
