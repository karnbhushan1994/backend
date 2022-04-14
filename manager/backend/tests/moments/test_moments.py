from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase


class MomentsTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tagg",
            password="taggPassword!123",
            first_name="tagg",
            last_name="tagg",
            email="tagg@gmail.com",
        )
        self.client = APIClient()
        self.token = Token.objects.get(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.token))
        self.moments_api = "/api/moments/"
        self.dummy_user_id = self.user.id
        self.dummy_moment = "Early Life"
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    # Upload moments
    def test_upload_blank_user_id(self):
        data = {}
        response = self.client.post(self.moments_api, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual("user_id is required", response.data)

    def test_upload_blank_moment(self):
        data = {"user_id": self.dummy_user_id}
        response = self.client.post(self.moments_api, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual("moment is required", response.data)

    def test_upload_no_captions(self):
        data = {"user_id": self.dummy_user_id, "moment": self.dummy_moment}
        response = self.client.post(self.moments_api, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual("captions is required", response.data)

    def test_upload_no_images(self):
        data = {
            "user_id": self.dummy_user_id,
            "moment": self.dummy_moment,
            "captions": "{}",
        }
        response = self.client.post(self.moments_api, data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual("No images were found to be uploaded", response.data)

    # Retrieve moments
    def test_retrieve_blank_user_id(self):
        data = {}
        response = self.client.get(self.moments_api, data)
        self.assertEqual(response.status_code, 405)

    def test_retrieve_incorrect_user(self):
        data = {"moment": self.dummy_moment}
        response = self.client.get(self.moments_api + "/" + "edededededed", data)
        self.assertEqual(response.status_code, 404)

    # TODO
    # Add multiple test after having a infrastructure for proper testing
    # Infrastructure : A store for images (Off the top of my mind)
