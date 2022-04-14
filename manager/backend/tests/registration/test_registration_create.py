from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class UserRegistrationTest(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="tagg_123",
            password="taggPassword!123",
            first_name="tagg",
            last_name="tagg",
            email="tagg@gmail.com",
        )
        self.register_urls = "/api/register/"
        self.client = APIClient()
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_create_user(self):

        data = {
            "first_name": "John",
            "last_name": "Carter, Jr.",
            "username": "lilwayne",
            "email": "wayne@gmail.com",
            "password": "Password@1234",
        }

        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            201,
        )
        self.assertEqual(
            self.client.post(self.register_urls, data={}, format="json").status_code,
            400,
        )

    def test_validate_first_name(self):

        data = {
            "first_name": "John Nolan",
            "last_name": "tagg",
            "username": "jhn_123",
            "email": "jhn1234@gmail.com",
            "password": "taggPassword!123",
        }

        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            201,
        )

        data["first_name"] = ""
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["first_name"] = "Jake123 "
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

    def test_validate_last_name(self):

        data = {
            "first_name": "John Nolan",
            "last_name": "Carter, Jr.",
            "username": "jhn_123",
            "email": "jhn1234@gmail.com",
            "password": "taggPassword!123",
        }

        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            201,
        )

        data["last_name"] = ""
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["last_name"] = "Fromm_"
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

    def test_validate_username(self):
        data = {
            "first_name": "tagg",
            "last_name": "tagg",
            "username": "",
            "email": "tagg1234@gmail.com",
            "password": "taggPassword!123",
        }

        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["username"] = "tagg"
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["username"] = "tagg_123"
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["username"] = "tagg_1234"
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            201,
        )

    def test_validate_email(self):

        data = {
            "first_name": "tagg",
            "last_name": "tagg",
            "username": "tagg_1234",
            "email": "",
            "password": "taggPassword!123",
        }

        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["email"] = "tagg@gmail.com"
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["email"] = "tagg"
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["email"] = "tagg1234@gmail.com"
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            201,
        )

    def test_validate_password(self):
        data = {
            "first_name": "tagg",
            "last_name": "tagg",
            "username": "tagg_1234",
            "email": "tagg1234@gmail.com",
            "password": "tagg1234",
        }

        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )

        data["password"] = ""
        self.assertEqual(
            self.client.post(self.register_urls, data=data, format="json").status_code,
            400,
        )
