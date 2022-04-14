import json
import logging
from ..profile.utils import allow_to_view_private_content

from django.utils import timezone
from .utils import Socials, Social_URLs, get_linked_socials
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings
from django.http import HttpResponse
from requests_oauthlib import OAuth1Session
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..common.validator import check_is_valid_parameter, get_response
from .models import SocialLink, TaggUser


class LinkedSocialsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(LinkedSocialsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk=None):
        try:
            tagg_user = TaggUser.objects.get(id=pk)
            linked_socials = get_linked_socials(tagg_user)
            response = {"linked_socials": linked_socials}
            return Response(response, status=status.HTTP_200_OK)
        except TaggUser.DoesNotExist:
            self.logger.exception("Tagg user does not exist.")
            return Response(
                "Tagg user does not exist.", status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as err:
            self.logger.error("Problem occured populating linked socials")
            return Response(
                "Problem occured populating linked socials",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LinkFBViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(LinkFBViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        # See https://developers.facebook.com/docs/facebook-login/manually-build-a-login-flow/#exchangecode
        try:
            body = json.loads(request.body)
            user_id = request.user.id
            callback_url = body["callback_url"]
        except KeyError:
            self.logger.exception("Missing parameters")
            return Response("Missing parameters", status=status.HTTP_400_BAD_REQUEST)

        # taggid://callback?code=xxxxxxxxxxxx#_=_
        token = parse_qs(urlparse(callback_url).query)["code"]

        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "code": token,
        }
        response = requests.get(
            "https://graph.facebook.com/v8.0/oauth/access_token", params=params
        )
        if response.status_code // 100 != 2:
            self.logger.error("Could not link with Facebook API")
            return Response(
                "Could not link with Facebook API",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        body = response.json()

        long_lived_token = body["access_token"]

        # Now we try to grab the user_id using the debug_token graph api
        # See https://developers.facebook.com/docs/graph-api/reference/v8.0/debug_token
        # and https://developers.facebook.com/docs/facebook-login/access-tokens/#apptokens
        params = {
            "input_token": long_lived_token,
            "access_token": settings.FACEBOOK_APP_ACCESS_ID,
            "fields": "user_id",
        }
        response = requests.get(
            "https://graph.facebook.com/v8.0/debug_token", params=params
        )
        if response.status_code // 100 != 2:
            self.logger.error("Unable to fetch user information")
            return Response(
                "Unable to fetch user information",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        body = response.json()
        fb_user_id = body["data"]["user_id"]

        try:
            tagg_user = TaggUser.objects.get(id=user_id)
            request_user = request.user
            if tagg_user.username != request_user.username:
                return Response(
                    "Unauthorized user: " + request_user.username,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            social_link, _ = SocialLink.objects.get_or_create(user_id=tagg_user)
            social_link.fb_user_id = fb_user_id
            social_link.fb_access_token = long_lived_token
            social_link.fb_token_date = timezone.now()
            social_link.save()

        except TaggUser.DoesNotExist:
            self.logger.exception("Tagg user does not exist.")
            return Response(
                "Tagg user does not exist.", status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            "Long-lived token obtained, account created and stored!",
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def update(self, request, pk=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def partial_update(self, request, pk=None):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def destroy(self, request, pk=None):
        if pk != request.user.id:
            return get_response(data="User does not match request user", type=403)
        try:
            if pk:
                user_id = pk
            else:
                body = json.loads(request.body)
                user_id = body["userID"]

        except KeyError:
            self.logger.exception("Missing parameters")
            return Response("Missing parameters", status=status.HTTP_400_BAD_REQUEST)

        try:
            tagg_user = TaggUser.objects.get(id=user_id)
            social_link = SocialLink.objects.get(user_id=tagg_user)
            if tagg_user.username != request.user.username:
                self.logger.error("Unauthorized user: " + request.user.username)
                return Response(
                    "Unauthorized user: " + request.user.username,
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if social_link and social_link.fb_user_id:
                social_link.fb_user_id = ""
                social_link.fb_access_token = ""
                social_link.save()
            else:
                self.logger.error("FB not linked")
                return Response("FB not linked", status=status.HTTP_400_BAD_REQUEST)
        except TaggUser.DoesNotExist:
            self.logger.exception("Tagg user does not exist.")
            return Response(
                "Tagg user does not exist.", status=status.HTTP_400_BAD_REQUEST
            )

        return Response("FB access token deleted", status=status.HTTP_200_OK)

    def list(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class LinkInstagramViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(LinkInstagramViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    """
    Social Linking Flow for Instagram

    Step 1: 
        Receive *auth_token* from frontend
    Step 2: 
        Contact Instagram with the *auth_token* in exchange for the user-specific *short_lived_token* and *ig_user_id*
    Step 3: 
        Contact Instagram again with the *short_lived_token* in exchange for the *long_lived_token*
    """

    def create(self, request):
        try:
            # Step 1
            body = json.loads(request.body)
            if not check_is_valid_parameter("callback_url", body):
                return get_response(data="callback_url is required", type=400)
            callback_url = body["callback_url"]

            # taggid://callback?code=xxxxxxxxxxxx#_
            token = parse_qs(urlparse(callback_url).query)["code"]

            # Step 2
            payload = {
                "client_id": settings.INSTAGRAM_APP_ID,
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": settings.OAUTH_REDIRECT_URI,
                "code": token,
            }
            response = requests.post(
                "https://api.instagram.com/oauth/access_token", data=payload
            )
            if response.status_code // 100 == 4:
                self.logger.error("Unable to link with Instagram API")
                return get_response(data="Unable to link with Instagram API", type=400)
            body = response.json()
            short_lived_token = body["access_token"]
            ig_user_id = body["user_id"]

            # Step 3
            params = {
                "grant_type": "ig_exchange_token",
                "client_secret": settings.INSTAGRAM_APP_SECRET,
                "access_token": short_lived_token,
            }
            response = requests.get(
                "https://graph.instagram.com/access_token", params=params
            )
            if response.status_code // 100 == 4:
                self.logger.error("Unable to link with Instagram API")
                return get_response(data="Unable to link with Instagram API", type=400)
            body = response.json()
            long_lived_token = body["access_token"]

            # Finally, we save the social link for the user
            social_link, _ = SocialLink.objects.get_or_create(user_id=request.user)
            social_link.ig_user_id = ig_user_id
            social_link.ig_access_token = long_lived_token
            social_link.ig_token_date = timezone.now()
            social_link.save()

            return get_response(
                data="Long-lived token obtained, account created and stored!", type=201
            )

        except TaggUser.DoesNotExist:
            self.logger.exception("Tagg user does not exist")
            return get_response(data="Tagg user does not exist", type=400)
        except Exception as error:
            self.logger.exception("There was a problem processing your request")
            return get_response(
                data="There was a problem processing your request", type=500
            )
        except:
            self.logger.exception("Unknown exception while linking Instagram")
            return get_response(
                data="There was a problem processing your request", type=500
            )

    def destroy(self, request, pk=None):
        if pk != request.user.id:
            self.logger.error("User does not match request user")
            return get_response(data="User does not match request user", type=403)
        try:
            if pk:
                user_id = pk
            else:
                body = json.loads(request.body)
                user_id = body["userID"]
        except KeyError:
            self.logger.exception("Missing parameters")
            return Response("Missing parameters", status=status.HTTP_400_BAD_REQUEST)

        try:
            tagg_user = TaggUser.objects.get(id=user_id)
            social_link = SocialLink.objects.get(user_id=tagg_user)
            if social_link and social_link.ig_user_id:
                social_link.ig_user_id = ""
                social_link.ig_access_token = ""
                social_link.save()
            else:
                self.logger.error("IG not linked")
                return Response("IG not linked", status=status.HTTP_400_BAD_REQUEST)

        except TaggUser.DoesNotExist:
            self.logger.exception("Tagg user does not exist")
            return Response(
                "Tagg user does not exist.", status=status.HTTP_400_BAD_REQUEST
            )

        return Response("IG access token deleted", status=status.HTTP_200_OK)

    def list(self, request):
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


class CallbackRedirectViewset(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def list(self, request):
        response = HttpResponse("", status=302)
        response["Location"] = settings.OAUTH_REDIRECT_URI
        return response


class InitialTwitterRequestViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(InitialTwitterRequestViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    # See https://developer.twitter.com/en/docs/authentication/guides/log-in-with-twitter
    def list(self, request):
        try:
            # Step 1
            # obtaining a request_token
            # In this initial request, the resource owner key and secret
            # (field 3 and 4) will be our access token that we created
            # in the twitter console.
            twitter = OAuth1Session(
                settings.TWITTER_API_KEY,
                settings.TWITTER_API_SECRET,
                settings.TWITTER_ACCESS_TOKEN,
                settings.TWITTER_ACCESS_TOKEN_SECRET,
            )
            response = twitter.post("https://api.twitter.com/oauth/request_token")
            if response.status_code // 100 != 2:
                raise TwitterAPIException("Unable to contact Twitter API")
            parsed = parse_qs(response.content.decode("ascii"))
            if not parsed["oauth_callback_confirmed"][0] == "true":
                raise TwitterAPIException("Invalid callback")
            oauth_token = parsed["oauth_token"][0]
            oauth_token_secret = parsed["oauth_token_secret"][0]

            # saving this temporary token pair in db for Step 3 (in api/link-twitter)
            social_link, _ = SocialLink.objects.get_or_create(user_id=request.user)
            social_link.twitter_oauth_token = oauth_token
            social_link.twitter_oauth_token_secret = oauth_token_secret
            social_link.save()

            # returning a redirect to twitter login to complete Step 2
            # We only really need the url location here, keeping it a redirect
            # to support browser sign-ins
            response = HttpResponse("", status=302)
            response[
                "Location"
            ] = f"https://api.twitter.com/oauth/authenticate?oauth_token={oauth_token}"
            return response

        except (TwitterAPIException, KeyError) as error:
            self.logger.exception("Something went wrong with Twitter API")
            return Response(
                "Something went wrong with Twitter API",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as error:
            self.logger.exception("Unable to obtaina request token")
            return Response(
                "Unable to obtain a request token",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class LinkTwitterViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(LinkTwitterViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    # See https://developer.twitter.com/en/docs/authentication/guides/log-in-with-twitter
    def create(self, request):
        try:
            body = json.loads(request.body)
            if not check_is_valid_parameter("callback_url", body):
                return get_response(data="callback_url is required", type=400)
            callback_url = body["callback_url"]

            # parse info from body's callback url
            # taggid://callback?oauth_token=xxx&oauth_verifier=xxx
            parsed = parse_qs(urlparse(callback_url).query)
            oauth_token = parsed["oauth_token"][0]
            oauth_verifier = parsed["oauth_verifier"][0]

            # retrieve the temporary token pair from db to complete last step
            social_link, _ = SocialLink.objects.get_or_create(user_id=request.user)
            stored_oauth_token = social_link.twitter_oauth_token
            stored_oauth_token_secret = social_link.twitter_oauth_token_secret

            if oauth_token != stored_oauth_token:
                raise Exception("Request token does not equal to stored token")

            # Step 3: exchange token for long-lived token
            twitter = OAuth1Session(
                settings.TWITTER_API_KEY,
                settings.TWITTER_API_SECRET,
                oauth_token,
                stored_oauth_token_secret,
            )
            params = {"oauth_verifier": oauth_verifier}
            response = twitter.post(
                "https://api.twitter.com/oauth/access_token", params=params
            )

            if response.status_code // 100 != 2:
                self.logger.error(response)
                raise Exception("Unable to obtain long-lived token from twitter")

            parsed = parse_qs(response.content.decode("utf-8"))
            ll_oauth_token = parsed["oauth_token"][0]
            ll_oauth_token_secret = parsed["oauth_token_secret"][0]
            twitter_user_id = parsed["user_id"][0]
            twitter_screen_name = parsed["screen_name"][0]

            # Now we store these long-lived token pair for future use
            social_link.twitter_oauth_token = ll_oauth_token
            social_link.twitter_oauth_token_secret = ll_oauth_token_secret
            social_link.twitter_user_id = twitter_user_id
            social_link.twitter_screen_name = twitter_screen_name
            social_link.save()

            return Response(
                "Long-lived token obtained, account created and stored!",
                status=status.HTTP_201_CREATED,
            )

        except Exception as error:
            self.logger.exception("Unable to link with twitter")
            return Response(
                "Unable to link with twitter",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TwitterAPIException(Exception):
    pass


class NonIntegratedSocialLinkBase:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def handle_create(self, request, social_type):
        try:
            body = json.loads(request.body)

            if not check_is_valid_parameter("username", body):
                return get_response("username is required", type=400)

            social_link, _ = SocialLink.objects.get_or_create(user_id=request.user)

            if social_type == Socials.Snapchat:
                social_link.snapchat_username = body["username"]
            elif social_type == Socials.TikTok:
                social_link.tiktok_username = body["username"]
            else:
                msg = "Unsupported non-integrated social type"
                self.logger.error(msg)
                raise Exception(msg)

            social_link.save()

            return get_response("Success", type=200)
        except Exception as error:
            self.logger.exception(error)
            return get_response("Request failed with unknown reason", type=500)

    def handle_retrieve(self, request, pk, social_type):
        try:
            social_link = SocialLink.objects.get(user_id=pk)
            user = TaggUser.objects.get(id=pk)
            username = ""

            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_204_NO_CONTENT)

            if social_type == Socials.Snapchat:
                username = social_link.snapchat_username
            elif social_type == Socials.TikTok:
                username = social_link.tiktok_username
            else:
                raise Exception("Unsupported non-integrated social type")

            if not username:
                return get_response("URL does not exist", type=404)

            if social_type in Social_URLs:
                url = Social_URLs[social_type](username)
            else:
                raise Exception("Unsupported non-integrated social type")

            return Response({"url": url}, status=status.HTTP_200_OK)
        except Exception as error:
            self.logger.exception(error)
            return get_response("Request failed with unknown reason", type=500)

    def handle_destroy(self, request, pk, social_type):
        try:
            if not str(request.user.id) == pk:
                self.logger.error("Unauthorized")
                return get_response(data="Unauthorized", type=401)

            social_link = SocialLink.objects.get(user_id=pk)

            if social_type == Socials.Snapchat:
                social_link.snapchat_username = ""
            elif social_type == Socials.TikTok:
                social_link.tiktok_username = ""
            else:
                msg = "Unsupported non-integrated social type"
                self.logger.error(msg)
                raise Exception(msg)

            social_link.save()

            return get_response(data="Success", type=200)

        except Exception as error:
            self.logger.exception(error)
            return get_response("Request failed with unknown reason", type=500)


class LinkSnapchatViewSet(viewsets.ViewSet, NonIntegratedSocialLinkBase):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(LinkSnapchatViewSet, self).__init__(*args, **kwargs)
        NonIntegratedSocialLinkBase.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.social_type = Socials.Snapchat

    def create(self, request):
        return self.handle_create(request, self.social_type)

    def retrieve(self, request, pk=None):
        return self.handle_retrieve(request, pk, self.social_type)

    def destroy(self, request, pk=None):
        return self.handle_destroy(request, pk, self.social_type)


class LinkTikTokViewSet(viewsets.ViewSet, NonIntegratedSocialLinkBase):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(LinkTikTokViewSet, self).__init__(*args, **kwargs)
        NonIntegratedSocialLinkBase.__init__(self)
        self.logger = logging.getLogger(__name__)
        self.social_type = Socials.TikTok

    def create(self, request):
        return self.handle_create(request, self.social_type)

    def retrieve(self, request, pk=None):
        return self.handle_retrieve(request, pk, self.social_type)

    def destroy(self, request, pk=None):
        return self.handle_destroy(request, pk, self.social_type)
