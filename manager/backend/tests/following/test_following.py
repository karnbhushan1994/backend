from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class UserFollowingTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user1 = User.objects.create_user(
            username="tagg_123",
            password="taggPassword!123",
            first_name="tagg",
            last_name="tagg",
            email="tagg@gmail.com",
        )

        self.User2 = User.objects.create_user(
            username="lilwayne",
            password="Password@1234",
            first_name="John",
            last_name="Carter, Jr.",
            email="wayne@gmail.com",
        )
        self.token2 = Token.objects.get(user=self.User2)

        self.user3 = User.objects.create_user(
            username="jhn_123",
            password="taggPassword!123",
            first_name="John Nolan",
            last_name="Dave",
            email="jhn1234@gmail.com",
        )
        self.token3 = Token.objects.get(user=self.user3)

        self.follow_urls = "/api/follow/"
        self.unfollow_urls = "/api/unfollow/"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_follow_user(self):
        data = {"followed": "tagg_123", "follower": "jhn_123"}
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token3))
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            201,
        )
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            400,
        )

        data["follower"] = "lilwayne"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token2))
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            201,
        )

        data["followed"] = "abc_123"
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            400,
        )

        data["follower"] = "mark_25"
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            400,
        )

        data["followed"] = ""
        data["follower"] = ""
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            400,
        )

    def test_unfollow_user(self):
        data = {"followed": "tagg_123", "follower": "lilwayne"}
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token2))
        self.assertEqual(
            self.client.post(self.follow_urls, data=data, format="json").status_code,
            201,
        )
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            200,
        )

        data["follower"] = "jhn_123"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token3))
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            400,
        )

        data["followed"] = "abc_123"
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            400,
        )

        data["followed"] = ""
        data["follower"] = ""
        self.assertEqual(
            self.client.post(self.unfollow_urls, data=data, format="json").status_code,
            400,
        )
