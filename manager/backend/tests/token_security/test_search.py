from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class UserSearchTest(APITestCase):
    def setUp(self):

        User = get_user_model()

        self.user1 = User.objects.create_user(
            username="user1",
            password="Password@user1",
            first_name="user",
            last_name="one",
            email="user1@gmail.com",
        )
        self.token1 = Token.objects.get(user=self.user1)

        self.User2 = User.objects.create_user(
            username="user2",
            password="Password@user2",
            first_name="user",
            last_name="two",
            email="user2@gmail.com",
        )

        self.User3 = User.objects.create_user(
            username="user3",
            password="Password@user3",
            first_name="user",
            last_name="three",
            email="user3@gmail.com",
        )

        self.search_url = "/api/search/"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_search(self):
        params = {"query": "user"}
        # Case 1: No credentials attached
        self.client.credentials()
        self.assertEqual(self.client.get(self.search_url, params).status_code, 401)

        # Case 2: Value = ""
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(self.client.get(self.search_url, params).status_code, 401)

        # Case 3: Value = "Token "
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        self.assertEqual(self.client.get(self.search_url, params).status_code, 401)

        # Case 4: Value = "Token <random_string>"
        self.client.credentials(HTTP_AUTHORIZATION="Token randomstring123")
        self.assertEqual(self.client.get(self.search_url, params).status_code, 401)

        # [Accepted] Case 5: Value = "Token <taggUser's_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token1))
        self.assertEqual(self.client.get(self.search_url, params).status_code, 200)
