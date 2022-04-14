# from django.contrib.auth import get_user_model
# from rest_framework.test import APIClient, APITestCase
# from rest_framework.authtoken.models import Token
# from ...social_linking.models import SocialLink


# class SocialPostsTest(APITestCase):

#     def setUp(self):

#         User = get_user_model()

#         self.user1 = User.objects.create_user(
#             username='user1', password='Password@user1', first_name='user',
#             last_name='one', email='user1@gmail.com')
#         self.token1 = Token.objects.get(user=self.user1)

#         self.social_link = SocialLink.objects.create(user_id=self.user1)
#         self.social_link.fb_user_id = "random_value"
#         self.social_link.fb_access_token = "random_value"
#         self.social_link.ig_user_id = "enter ig user id"
#         self.social_link.ig_access_token = "enter ig long lived token"
#         self.social_link.save()

#         self.ig_posts_url = '/api/posts-ig/{}'.format(self.user1.id)+'/'
#         self.client = APIClient()
#         return super().setUp()

#     def tearDown(self):
#         return super().tearDown()

#     def test_retrieval(self):
#         data = {"userID": self.user1.id,
#                 "IGUserID": "enter ig user id",
#                 "accessToken": "enter ig long lived token"}

#         # Case 1: No credentials attached
#         self.client.credentials()
#         self.assertEqual(self.client.get(
#             self.ig_posts_url, data=data, format="json").status_code, 401)

#         # Case 2: Value = ""
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         self.assertEqual(self.client.get(
#             self.ig_posts_url, data=data, format="json").status_code, 401)

#         # Case 3: Value = "Token "
#         self.client.credentials(HTTP_AUTHORIZATION='Token ')
#         self.assertEqual(self.client.get(
#             self.ig_posts_url, data=data, format="json").status_code, 401)

#         # Case 4: Value = "Token <random_string>"
#         self.client.credentials(HTTP_AUTHORIZATION='Token randomstring123')
#         self.assertEqual(self.client.get(
#             self.ig_posts_url, data=data, format="json").status_code, 401)

#         # [Accepted] Case 5: Value = "Token <taggUser's_token>"
#         self.client.credentials(
#             HTTP_AUTHORIZATION='Token {}'.format(self.token1))
#         self.assertEqual(self.client.get(
#             self.ig_posts_url, data=data, format="json").status_code, 200)
