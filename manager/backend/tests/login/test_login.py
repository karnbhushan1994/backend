from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase


class TestUserLogin(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tagg",
            password="taggPassword!123",
            first_name="tagg",
            last_name="tagg",
            email="tagg@gmail.com",
        )
        self.token = Token.objects.get(user=self.user)

        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_user_can_login(self):
        self.assertTrue(self.user.is_authenticated)

        # test login with correct credentials returns true
        self.assertTrue(self.client.login(username="tagg", password="taggPassword!123"))
        self.assertTrue(check_password("taggPassword!123", self.user.password))

        # test login with incorrect credentials returns false
        self.assertFalse(self.client.login(username="tagg", password="wrongPassword"))
        self.assertFalse(
            self.client.login(username="wrongUsername", password="password")
        )
        self.assertFalse(check_password("wrongpassword", self.user.password))

    def test_user_can_logout(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))
        response = self.client.get("/api/logout/")
        self.assertEquals(response.status_code, 200)
