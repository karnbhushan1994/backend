import json

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


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

    """
    Tests an attempt to access this endpoint through an invalid request type.
    In this case, a POST request.
  """

    def test_bad_endpoint_small_pic(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.Randomtoken))
        response = self.client.post(self.small_pic)
        self.assertEqual(response.status_code, 405)

    def test_bad_endpoint_large_pic(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.Randomtoken))
        response = self.client.post(self.large_pic)
        self.assertEqual(response.status_code, 405)
