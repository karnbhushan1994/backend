import json
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient, APITestCase


class VerifyInvitationCodeTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.api_generate = "/api/create-code/"
        self.api_route = "/api/verify-code/"

    def test_verify_code_valid_code(self):
        create = self.client.post(self.api_generate)
        val = create.data["code"]
        response1 = self.client.delete(self.api_route + val + "/")
        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response1.data, "Code Verified and Deleted")

    def test_verify_code_invalid_code(self):
        val = "ABCDEF"
        response1 = self.client.delete(self.api_route + val + "/")
        self.assertEqual(response1.data, "Failure")
        self.assertEqual(response1.status_code, 400)

    def test_verify_code_expires_code(self):
        create = self.client.post(self.api_generate)
        val = create.data["code"]
        response1 = self.client.delete(self.api_route + val + "/")
        response2 = self.client.delete(self.api_route + val + "/")
        self.assertEqual(response2.data, "Failure")
        self.assertEqual(response2.status_code, 400)
