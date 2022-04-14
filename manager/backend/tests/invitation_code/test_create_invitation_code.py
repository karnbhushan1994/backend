import json
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class InvitationCodeTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.api_route = "/api/create-code/"

    def test_check_code(self):
        response = self.client.post(self.api_route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Created Invitation Code")

    def test_code_uppercase(self):
        response = response = self.client.post(self.api_route)
        self.assertEqual(response.data["code"].isupper(), True)
