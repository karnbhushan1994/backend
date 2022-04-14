from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient, APITestCase
from fcm_django.models import FCMDevice
from ...models import TaggUser


class TestUserLogin(APITestCase):
    def setUp(self):
        self.device = FCMDevice()
        self.device.device_id = "device id"
        self.device.registration_id = "Insert registration id/device token"
        self.device.type = "ios/android"
        self.device.name = "User's Phone Name"
        self.device.user = TaggUser.objects.all().last()
        self.device.save()

        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_user_can_login(self):
        self.device.send_message(title="Title", body="Message")
