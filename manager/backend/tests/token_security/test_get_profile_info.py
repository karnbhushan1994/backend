import json

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class GetProfileTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="user1",
            password="Password!123",
            first_name="User",
            last_name="One",
            email="user1@email.com",
        )
        self.random_user = User.objects.create_user(
            username="user2",
            password="Password!123",
            first_name="User",
            last_name="Two",
            email="user2@email.com",
        )

        self.token = Token.objects.get(user=self.random_user)
        self.endpoint = "/api/user-profile-info/" + str(self.user.id) + "/"

        self.client = APIClient()

        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_good_endpoint(self):

        # Case 1: No credentials attached
        self.client.credentials()
        self.assertEqual(self.client.get(self.endpoint).status_code, 401)

        # Case 2: Value = ""
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(self.client.get(self.endpoint).status_code, 401)

        # Case 3: Value = "Token "
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        self.assertEqual(self.client.get(self.endpoint).status_code, 401)

        # Case 4: Value = "Token <random_string>"
        self.client.credentials(HTTP_AUTHORIZATION="Token random_string")
        self.assertEqual(self.client.get(self.endpoint).status_code, 401)

        # [Accepted] Case 5: Value = "Token <taggUser's_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.assertEqual(self.client.get(self.endpoint).status_code, 200)
