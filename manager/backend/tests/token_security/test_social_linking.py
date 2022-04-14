# from django.contrib.auth import get_user_model
# from rest_framework.test import APIClient, APITestCase
# from rest_framework.authtoken.models import Token


# class SocialLinkingTest(APITestCase):

#     def setUp(self):

#         User = get_user_model()

#         self.user1 = User.objects.create_user(
#             username='user1', password='Password@user1', first_name='user',
#             last_name='one', email='user1@gmail.com')
#         self.token1 = Token.objects.get(user=self.user1)

#         self.user2 = User.objects.create_user(
#             username='user2', password='Password@user2', first_name='user',
#             last_name='two', email='user2@gmail.com')
#         self.token2 = Token.objects.get(user=self.user2)

#         self.ig_link_url = '/api/link-ig/'
#         self.fb_link_url = '/api/link-fb/'

#         self.client = APIClient()
#         return super().setUp()

#     def tearDown(self):
#         return super().tearDown()

#     def test_ig_linking(self):
#         data = {
#             "userID": self.user1.id,
#             "IGUserID": "enter ig user id",
#             "accessToken": "enter ig long lived token"
#         }
#         # Case 1: No credentials attached
#         self.client.credentials()
#         self.assertEqual(self.client.post(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # Case 2: Value = ""
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         self.assertEqual(self.client.post(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # Case 3: Value = "Token "
#         self.client.credentials(HTTP_AUTHORIZATION='Token ')
#         self.assertEqual(self.client.post(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # Case 4: Value = "Token <random_string>"
#         self.client.credentials(HTTP_AUTHORIZATION='Token randomstring123')
#         self.assertEqual(self.client.post(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # [Accepted] Case 5: Value = "Token <taggUser's_token>"
#         self.client.credentials(
#             HTTP_AUTHORIZATION='Token {}'.format(self.token1))
#         self.assertEqual(self.client.post(
#             self.ig_link_url, data, format="json").status_code, 201)

#     def test_ig_unlinking(self):
#         data = {
#             "userID": self.user1.id,
#             "IGUserID": "enter ig user id",
#             "accessToken": "enter ig long lived token"
#         }
#         self.client.credentials(
#             HTTP_AUTHORIZATION='Token {}'.format(self.token1))
#         self.assertEqual(self.client.post(
#             self.ig_link_url, data, format="json").status_code, 201)

#         data = {
#             "userID": self.user1.id
#         }
#         # Case 1: No credentials attached
#         self.client.credentials()
#         self.assertEqual(self.client.delete(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # Case 2: Value = ""
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         self.assertEqual(self.client.delete(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # Case 3: Value = "Token "
#         self.client.credentials(HTTP_AUTHORIZATION='Token ')
#         self.assertEqual(self.client.delete(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # Case 4: Value = "Token <random_string>"
#         self.client.credentials(HTTP_AUTHORIZATION='Token randomstring123')
#         self.assertEqual(self.client.delete(
#             self.ig_link_url, data, format="json").status_code, 401)

#         # [Accepted] Case 5: Value = "Token <taggUser's_token>"
#         self.client.credentials(
#             HTTP_AUTHORIZATION='Token {}'.format(self.token1))
#         self.assertEqual(self.client.delete(
#             self.ig_link_url, data, format="json").status_code, 200)

#     def test_fb_linking(self):
#         data = {
#             "userID": self.user2.id,
#             "FBUserID": "fb user id",
#             "accessToken": "enter fb long lived token"
#         }
#         # Case 1: No credentials attached
#         self.client.credentials()
#         self.assertEqual(self.client.post(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # Case 2: Value = ""
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         self.assertEqual(self.client.post(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # Case 3: Value = "Token "
#         self.client.credentials(HTTP_AUTHORIZATION='Token ')
#         self.assertEqual(self.client.post(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # Case 4: Value = "Token <random_string>"
#         self.client.credentials(HTTP_AUTHORIZATION='Token randomstring123')
#         self.assertEqual(self.client.post(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # [Accepted] Case 5: Value = "Token <taggUser's_token>"
#         self.client.credentials(
#             HTTP_AUTHORIZATION='Token {}'.format(self.token2))
#         self.assertEqual(self.client.post(
#             self.fb_link_url, data, format="json").status_code, 201)

#     def test_fb_unlinking(self):

#         data = {
#             "userID": self.user2.id,
#             "FBUserID": "enter fb user id",
#             "accessToken": "enter fb long lived token"
#         }

#         self.client.credentials(
#             HTTP_AUTHORIZATION='Token {}'.format(self.token2))
#         self.assertEqual(self.client.post(
#             self.fb_link_url, data, format="json").status_code, 201)

#         data = {
#             "userID": self.user2.id
#         }

#         # Case 1: No credentials attached
#         self.client.credentials()
#         self.assertEqual(self.client.delete(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # Case 2: Value = ""
#         self.client.credentials(HTTP_AUTHORIZATION='')
#         self.assertEqual(self.client.delete(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # Case 3: Value = "Token "
#         self.client.credentials(HTTP_AUTHORIZATION='Token ')
#         self.assertEqual(self.client.delete(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # Case 4: Value = "Token <random_string>"
#         self.client.credentials(HTTP_AUTHORIZATION='Token randomstring123')
#         self.assertEqual(self.client.delete(
#             self.fb_link_url, data, format="json").status_code, 401)

#         # [Accepted] Case 5: Value = "Token <taggUser's_token>"
#         self.client.credentials(
#             HTTP_AUTHORIZATION='Token {}'.format(self.token2))
#         self.assertEqual(self.client.delete(
#             self.fb_link_url, data, format="json").status_code, 200)
