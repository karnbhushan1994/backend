import json
import io
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from PIL import Image


class GetProfilePicTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="johndoe@gmail,com",
            username="johndoe",
            password="ilov3jane!",
        )
        self.token = Token.objects.get(user=self.user)

        self.random_user = User.objects.create_user(
            username="user2",
            password="Password!123",
            first_name="User",
            last_name="Two",
            email="user2@email.com",
        )
        self.Randomtoken = Token.objects.get(user=self.random_user)

        self.client = APIClient()

        self.small_pic = "/api/small-profile-pic/" + str(self.user.id) + "/"
        self.large_pic = "/api/large-profile-pic/" + str(self.user.id) + "/"

        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_get_small_profile_pic(self):

        # Case 1: No credentials attached
        self.client.credentials()
        self.assertEqual(self.client.get(self.small_pic).status_code, 401)

        # Case 2: Value = ""
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(self.client.get(self.small_pic).status_code, 401)

        # Case 3: Value = "Token "
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        self.assertEqual(self.client.get(self.small_pic).status_code, 401)

        # Case 4: Value = "Token <random_string>"
        self.client.credentials(HTTP_AUTHORIZATION="Token random_string")
        self.assertEqual(self.client.get(self.small_pic).status_code, 401)

        # [Accepted] Case 5: Value = "Token <taggUser's_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.assertEqual(self.client.get(self.small_pic).status_code, 404)

    def test_get_large_profile_pic(self):

        # Case 1: No credentials attached
        self.client.credentials()
        self.assertEqual(self.client.get(self.large_pic).status_code, 401)

        # Case 2: Value = ""
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(self.client.get(self.large_pic).status_code, 401)

        # Case 3: Value = "Token "
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        self.assertEqual(self.client.get(self.large_pic).status_code, 401)

        # Case 4: Value = "Token <random_string>"
        self.client.credentials(HTTP_AUTHORIZATION="Token random_string")
        self.assertEqual(self.client.get(self.large_pic).status_code, 401)

        # [Accepted] Case 5: Value = "Token <taggUser's_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.Randomtoken))
        self.assertEqual(self.client.get(self.small_pic).status_code, 404)
