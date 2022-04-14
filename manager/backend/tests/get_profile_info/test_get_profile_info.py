import json

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token


class GetProfileTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="GhostBoy",
            password="G0ingGh0st!",
            first_name="Daniel",
            last_name="Fenton",
            email="danny@fenton.co",
        )
        self.token = Token.objects.get(user=self.user)
        self.endpoint = "/api/user-profile-info/" + str(self.user.id) + "/"
        self.edit_profile_endpoint = "/api/edit-profile/" + str(self.user.id) + "/"
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.client.patch(
            self.edit_profile_endpoint,
            {
                "biography": "I was just 14 when my parents built a very strange machine. #RearrangedMolecules",
                "website": "www.nick.com",
            },
        )

        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    """
    Generates a valid but (allegedly) non-existent user-id
  """

    def generateNonExistentID(self, id, replacementChar="1"):
        idString = str(id)
        for i in range(len(idString)):
            if idString[i] == "-":
                continue
            if idString[i] != replacementChar:
                return idString[:i] + replacementChar + idString[i + 1 :]

    """
    Tests an attempt to access this endpoint through an invalid request type.
    In this case, a POST request.
  """

    def test_bad_endpoint(self):
        response = self.client.post(self.endpoint)
        self.assertEqual(response.status_code, 405)

    """
    Tests an attempt to access this endpoint through a valid request type.
    For this endpoint, the only valid request type is GET.
  """

    def test_good_endpoint(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)

    """
    Tests whether endpoint returns the correct username.
  """

    def test_get_username(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "GhostBoy")

    """
    Tests whether endpoint returns the correct full name.
  """

    def test_get_fullname(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "Daniel Fenton")

    """
    Tests whether endpoint returns a 404 Not Found code for a non-existent user.
    User is specified by the user-id appended to the endpoint.
  """

    def test_non_existent_user(self):
        non_existent_id = self.generateNonExistentID(self.user.id)
        response = self.client.get(self.endpoint[:23] + non_existent_id + "/")
        self.assertEqual(response.status_code, 404)

    """
    Tests whether endpoint returns a 400 Bad Request code for an invalid user-id.
    The user-id in the test does not match the format of our user-ids.
  """

    def test_non_invalid_user(self):
        response = self.client.get(self.endpoint[:23] + "r3member/")
        self.assertEqual(response.status_code, 400)

    """
    Tests whether endpoint returns the correct biography.
  """

    def test_get_biography(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        test_biography = "I was just 14 when my parents built a very strange machine. #RearrangedMolecules"
        self.assertEqual(response.json()["biography"], test_biography)

    """
    Tests whether endpoint returns the correct website.
  """

    def test_get_website(self):
        response = self.client.get(self.endpoint)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["website"], "www.nick.com")
