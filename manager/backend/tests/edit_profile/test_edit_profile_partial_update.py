import json

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase

from ...edit_profile.utils import VALID_PROFILE_KEYS


class ProfileUpdateTest(APITestCase):
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
        self.api_route = "/api/edit-profile/"
        self.endpoint = self.api_route + str(self.user.id) + "/"
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def _get_test_user(self):
        return get_user_model().objects.get(id=str(self.user.id))

    def test_bad_endpoint(self):
        response = self.client.patch(self.api_route)
        self.assertEqual(response.status_code, 405)
        content = json.loads(response.content)
        self.assertEqual(content["detail"], 'Method "PATCH" not allowed.')

    def test_good_endpoint(self):
        response = self.client.patch(self.endpoint)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        for field in VALID_PROFILE_KEYS:
            self.assertEqual(content[field], "Not updated")

    def test_update_pictures(self):
        # TODO
        pass

    def test_birthday_invalid_format(self):
        birthday = "January 1, 2000"
        data = {"birthday": birthday}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 400)

    def test_birthday_invalid_date(self):
        birthday = "2020-01-01"
        data = {"birthday": birthday}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 400)

    def test_birthday_valid(self):
        birthday = "2000-01-01"
        data = {"birthday": birthday}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        for field in VALID_PROFILE_KEYS:
            if field == "birthday":
                self.assertEqual(content[field], "Updated")
                test_user = self._get_test_user()
                self.assertEqual(birthday, test_user.birthday.strftime("%Y-%m-%d"))
                continue
            self.assertEqual(content[field], "Not updated")

    def test_biography_invalid_length(self):
        biography = "Hello, John Doe here!" * 10
        data = {"biography": biography}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 400)

    def test_biography_valid(self):
        biography = "Hello, John Doe here!"
        data = {"biography": biography}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        for field in VALID_PROFILE_KEYS:
            if field == "biography":
                self.assertEqual(content[field], "Updated")
                test_user = self._get_test_user()
                self.assertEqual(biography, test_user.biography)
                continue
            self.assertEqual(content[field], "Not updated")

    def test_website_empty(self):
        website = ""
        data = {"website": website}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        for field in VALID_PROFILE_KEYS:
            if field == "website":
                self.assertEqual(content[field], "Updated")
                test_user = self._get_test_user()
                self.assertEqual(website, test_user.website)
                continue
            self.assertEqual(content[field], "Not updated")

    def test_website_invalid_length(self):
        website = "https://thetaggid.com/" * 10
        data = {"website": website}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 400)

    def test_website_invalid_format(self):
        website = "websitelinkimposter"
        data = {"website": website}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 400)

    def test_website_valid(self):
        website = "https://thetaggid.com/"
        data = {"website": website}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        for field in VALID_PROFILE_KEYS:
            if field == "website":
                self.assertEqual(content[field], "Updated")
                test_user = self._get_test_user()
                self.assertEqual(website, test_user.website)
                continue
            self.assertEqual(content[field], "Not updated")

    def test_gender_invalid_length(self):
        gender = "Pink fairy armadillo."
        data = {"gender": gender}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 400)

    def test_gender_valid(self):
        gender = "Pink fairy armadillo"
        data = {"gender": gender}
        response = self.client.patch(self.endpoint, data)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content)
        for field in VALID_PROFILE_KEYS:
            if field == "gender":
                self.assertEqual(content[field], "Updated")
                test_user = self._get_test_user()
                self.assertEqual(gender, test_user.gender)
                continue
            self.assertEqual(content[field], "Not updated")
