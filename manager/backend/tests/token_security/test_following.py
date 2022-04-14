from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class UserFollowingTest(APITestCase):
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
        self.token2 = Token.objects.get(user=self.User2)

        self.follow_urls = "/api/follow/"
        self.unfollow_urls = "/api/unfollow/"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_follow_user(self):

        data = {"followed": "user1", "follower": "user2"}

        # Case 1: No credentials attached
        self.client.credentials()
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 2: Value = ""
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 3: Value = "Token "
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 4: Value = "Token <random_string>"
        self.client.credentials(HTTP_AUTHORIZATION="Token randomstring123")
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 5: Value = "Token <followed_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token1))
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            400,
        )

        # [Accepted] Case 6: Value = "Token <follower_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token2))
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            201,
        )

    def test_unfollow_user(self):
        # Initial setup
        data = {"followed": "user1", "follower": "user2"}
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token2))
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            201,
        )

        # Case 1: No credentials attached
        self.client.credentials()
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 2: Value = ""
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 3: Value = "Token "
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 4: Value = "Token <random_string>"
        self.client.credentials(HTTP_AUTHORIZATION="Token randomstring123")
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            401,
        )

        # Case 5: Value = "Token <followed_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token1))
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            400,
        )

        # [Accepted] Case 6: Value = "Token <follower_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token2))
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            200,
        )
