from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase
from rest_framework.authtoken.models import Token
from ...social_linking.models import SocialLink


class EditProfileTest(APITestCase):
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
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.endpoint = "/api/edit-profile/" + str(self.user.id) + "/"

        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_edit_profile(self):
        birthday = "2000-01-01"
        data = {"birthday": birthday}

        # Case 1: No credentials attached
        self.client.credentials()
        self.assertEqual(self.client.patch(self.endpoint, data).status_code, 401)

        # Case 2: Value = ""
        self.client.credentials(HTTP_AUTHORIZATION="")
        self.assertEqual(self.client.patch(self.endpoint, data).status_code, 401)

        # Case 3: Value = "Token "
        self.client.credentials(HTTP_AUTHORIZATION="Token ")
        self.assertEqual(self.client.patch(self.endpoint, data).status_code, 401)

        # Case 4: Value = "Token <random_string>"
        self.client.credentials(HTTP_AUTHORIZATION="Token randomstring123")
        self.assertEqual(self.client.patch(self.endpoint, data).status_code, 401)

        # [Accepted] Case 5: Value = "Token <taggUser's_token>"
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 200)
