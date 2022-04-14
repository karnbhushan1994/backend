from django.test import TestCase

from ...models import TaggUser
from ...serializers import TaggUserSerializer


class SerializersTest(TestCase):
    def setUp(self):
        self.user = TaggUser.objects.create(
            username="john_123",
            password="taggPassword@123",
            first_name="John",
            last_name="Clark, Jr.",
            email="jclark12@gmail.com",
        )
        self.serializer_value = {
            "username": "john_123",
            "password": "taggPassword@123",
            "first_name": "John",
            "last_name": "Clark, Jr.",
            "email": "jclark12@gmail.com",
        }

        self.serialize = TaggUserSerializer(instance=self.serializer_value)
        return super().setUp()

    def tearDown(self):
        return super().tearDown()

    def test_serializers_data(self):
        data = self.serialize.data
        self.assertEqual(data["first_name"], self.user.first_name)
        self.assertEqual(data["last_name"], self.user.last_name)
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["email"], self.user.email)
        self.assertEqual(data["password"], self.user.password)
