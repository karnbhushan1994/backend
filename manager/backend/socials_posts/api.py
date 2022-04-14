import asyncio
import logging
from datetime import datetime
from html import unescape

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from requests_oauthlib import OAuth1Session
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..common.validator import get_response
from ..models import TaggUser
from ..profile.utils import allow_to_view_private_content
from ..social_linking.models import SocialLink


class IGPostsViewSet(viewsets.ViewSet):
    def __init__(self, *args, **kwargs):
        super(IGPostsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    # Given Tagg IG User ID returns list of IG post info
    # for user's latest 10 IG posts
    # GET request /api/ig_posts/userID="user_id"
    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        async def get_carousel_urls(token, post_id):
            params = {"access_token": token, "fields": "media_url"}
            response = requests.get(
                f"https://graph.instagram.com/{post_id}/children", params=params
            )
            if response.status_code // 100 != 2:
                print(response.json())
                print("Unable to fetch instagram carousel post data")
                return (post_id, [])
            body = response.json()
            # wrote a surprisingly safe code?!
            media_urls = [
                m.get("media_url") for m in body.get("data") or [] if m.get("media_url")
            ]
            return (post_id, media_urls)

        async def async_requests(*args):
            return await asyncio.gather(*args)

        if pk == None:
            self.logger.error("Tagg ID required")
            return Response("Tagg ID is required", status=status.HTTP_400_BAD_REQUEST)
        user_id = pk

        # get user Instagram ID from Tagg ID
        try:
            link = SocialLink.objects.get(user_id=user_id)

            if not (link.ig_user_id and link.ig_access_token):
                raise SocialLink.DoesNotExist()

            user = TaggUser.objects.get(id=pk)

            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_204_NO_CONTENT)

            if link.ig_user_id == "":
                return Response(
                    "Instagram not linked", status=status.HTTP_204_NO_CONTENT
                )

            # get user IG access token
            access_token = link.ig_access_token
            if access_token == None:
                self.logger.error("Tagg user does not have IG access token")
                return Response(
                    "Tagg user does not have IG access token",
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # retrieve latest 10 posts from IG user
            params = {
                "fields": "id,username,media_url,media_type,caption,timestamp,permalink",
                "access_token": access_token,
            }
            response = requests.get(
                "https://graph.instagram.com/me/media?", params=params
            )

            if "error" in response:
                self.logger.error("Could not retreive Instagram posts")
                link.ig_token_date = None
                link.save()
                return Response(
                    "Could not retreive Instagram posts",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            posts = response.json()

            if not posts.get("data"):
                self.logger.error("Could not retreive Instagram posts")
                link.ig_token_date = None
                link.save()
                return Response(
                    "Could not retreive Instagram posts",
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            ig_post_list = []

            carousel_request_queue = []

            for i, post in enumerate(posts.get("data")):
                # only grabbing 10 posts
                if i >= 10:
                    break
                # all posts should have type "IMAGE"
                if post.get("media_type") not in ["IMAGE", "CAROUSEL_ALBUM"]:
                    continue

                post_id = post.get("id")

                # we will need to make another request to fetch the rest of
                # the images
                if post_id and post.get("media_type") == "CAROUSEL_ALBUM":
                    carousel_request_queue.append(
                        get_carousel_urls(access_token, post_id)
                    )

                media_url = post.get("media_url")

                ig_post_info = {
                    "post_id": post_id,
                    "username": post.get("username"),
                    "media_url": [media_url] if media_url else [],
                    "media_type": "photo",
                    "caption": post.get("caption"),
                    "timestamp": post.get("timestamp"),
                    "permalink": post.get("permalink"),
                }

                ig_post_list.append(ig_post_info)

            # execute all queue'd up async requests
            carousel_request_results = asyncio.run(
                async_requests(*carousel_request_queue)
            )

            # convert results to a dict for easier/faster insertions
            carousel_results_dict = {}
            for post_id, media_urls in carousel_request_results:
                carousel_results_dict[post_id] = media_urls

            # inserting results back to the list
            for post in ig_post_list:
                post_id = post.get("post_id")
                if post_id in carousel_results_dict:
                    if not carousel_results_dict[post_id]:
                        # if the carousel result is empty, meaning it failed,
                        # we will just show the single image we already have from
                        # /me/media
                        continue
                    post["media_url"] = carousel_results_dict[post_id]

            response = {
                "handle": posts.get("data", [{}])[0].get("username"),
                # TODO we're not using this at the frontend for now
                "profile_pic": "",
                "posts": ig_post_list,
            }

            return Response(response, status=status.HTTP_200_OK)

        except SocialLink.DoesNotExist:
            return Response("Instagram not linked", status=status.HTTP_204_NO_CONTENT)
        except ValidationError:
            self.logger.exception("Invalid user Id")
            return Response(
                "Invalid user identifier.", status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as err:
            self.logger.exception("Problem occured while trying to retrieve posts")
            return get_response(
                data="Problem occured while trying to retrieve posts", type=500
            )


class FBPostsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(FBPostsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk=None):
        """
        Retrieves the most 10 recent facebook posts for a Tagg FB user.
        """

        async def get_name(token):
            # fetch the user's name as their "handle" for Facebook
            params = {"access_token": token}
            response = requests.get("https://graph.facebook.com/v8.0/me", params=params)
            if response.status_code // 100 != 2:
                self.logger.error(response.json())
                self.logger.error("Unable to retrieve facebook user name")
                # no name is fine
                return ""
            return response.json().get("name")

        async def get_profile_pic(token):
            # fetch the user's profile picture
            params = {"access_token": token, "redirect": False, "type": "large"}
            response = requests.get(
                "https://graph.facebook.com/v8.0/me/picture", params=params
            )
            if response.status_code // 100 != 2:
                self.logger.error(response.json())
                self.logger.error("Unable to retrieve facebook profile pic")
                # no profile pic is fine
                return ""
            return response.json().get("data", {}).get("url")

        # by default, the /me/posts API only returns the first image (we call
        # it default_image here), so if we want to get the entire album from
        # a post, we have to make a separate call for it.
        # case success:
        #      return the full list of urls
        # case partial-success:
        #   return just default_image in a list
        # case total-failure:
        #   return empty list
        async def get_media_urls(token, post_id):
            params = {"access_token": token}
            response = requests.get(
                f"https://graph.facebook.com/v8.0/{post_id}/attachments", params=params
            )
            if response.status_code // 100 != 2:
                print(response.json())
                print("Unable to retrieve facebook post's album data")
                return (post_id, [])
            body = response.json()
            # this is the first image of an album that *should* always be available
            default_image = (
                body.get("data", [{}])[0].get("media", {}).get("image", {}).get("src")
            )
            # if we have default, try to retreive the entire album
            if default_image:
                media_urls = [
                    media.get("media", {}).get("image", {}).get("src")
                    for media in body.get("data", [{}])[0]
                    .get("subattachments", {})
                    .get("data", [])
                ]
                if not media_urls:
                    media_urls = [default_image]
            else:
                media_urls = []
            return (post_id, media_urls)

        async def get_posts(token):
            # retrieve 10 most recent "posts" from facebook
            # See https://developers.facebook.com/docs/graph-api/reference/v8.0/user/feed
            # and https://developers.facebook.com/docs/graph-api/reference/post
            # If user has a post with an image, sometimes
            # Facebook will send us a post with text and image, and another
            # post with just the same image.
            # Workaround for this right now is to filter out all posts
            # with no message.
            params = {
                "access_token": token,
                # grabbing 15 posts in case some of them has no message
                "limit": 15,
                "fields": "message,created_time,permalink_url,is_hidden,type,full_picture",
            }
            response = requests.get(
                "https://graph.facebook.com/v8.0/me/posts", params=params
            )
            if response.status_code // 100 != 2:
                self.logger.error(response.content)
                # no posts is NOT fine
                raise Exception("Unable to retrieve facebook posts")
            posts = response.json().get("data") or []
            # filter out all posts with no message and not hidden
            posts = [
                post
                for post in posts
                if "message" in post and not post.get("is_hidden")
            ]

            # only return 10 posts
            # now we also try to fetch all media urls in an album (if there is one)
            posts = posts[:10]
            attachment_request_queue = []

            # attachment_request should perform on all posts with image.
            for post in posts[:10]:
                if post.get("type") == "photo" and post.get("id"):
                    attachment_request_queue.append(
                        get_media_urls(token, post.get("id"))
                    )

            attachment_result = await asyncio.gather(*attachment_request_queue)

            # convert to dictionary to easier/faster to insert
            result = {}
            for post_id, media_urls in attachment_result:
                result[post_id] = media_urls

            # we will put all the result in a new key called media_url
            # this new key should be present for all posts that has an image
            for post in posts:
                post_id = post.get("id")
                if post_id in result:
                    post["media_urls"] = result[post_id]

            return posts

        async def async_requests(*args):
            return await asyncio.gather(*args)

        # get user's facebook token
        try:
            if not pk:
                return get_response(data="pk is required", type=400)
            social_link = SocialLink.objects.get(user_id=pk)
            if not (social_link.fb_user_id and social_link.fb_access_token):
                raise SocialLink.DoesNotExist()
            token = social_link.fb_access_token
            user = TaggUser.objects.get(id=pk)

            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_204_NO_CONTENT)

            # O(N^2) requests async in get_posts
            # if a post is a photo type, we have to check if there are more
            # images in the post
            name, profile_pic, posts = asyncio.run(
                async_requests(
                    get_name(token), get_profile_pic(token), get_posts(token)
                )
            )

            formatted_posts = []

            for post in posts:
                # convert to our own type ('photo' | 'text')
                if post.get("type") in ["photo", "status"]:
                    media_type = "photo" if post.get("type") == "photo" else "text"
                else:
                    continue
                post_info = {
                    "post_id": post.get("id"),
                    "username": name,
                    "media_url": post.get("media_urls"),
                    "media_type": media_type,
                    "caption": post.get("message"),
                    "timestamp": post.get("created_time"),
                    "permalink": post.get("permalink_url"),
                }
                formatted_posts.append(post_info)

            response = {
                "handle": name,
                "profile_pic": profile_pic,
                "posts": formatted_posts,
            }
            return Response(response, status=status.HTTP_200_OK)

        except SocialLink.DoesNotExist:
            return Response("Facebook not linked", status=status.HTTP_204_NO_CONTENT)

        except Exception as error:
            self.logger.exception("Unable to fetch from Facebook API")
            return get_response(data="Unable to fetch from Facebook API", type=500)


class TwitterPostsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(TwitterPostsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk=None):
        """
        Retrieves the most 10 recent twitter posts for a Tagg FB user.
        """
        # get user's twitter token
        try:
            if not pk:
                self.logger.error("pk is required")
                return get_response(data="pk is required", type=400)
            social_link = SocialLink.objects.get(user_id=pk)
            if not (
                social_link.twitter_user_id
                and social_link.twitter_oauth_token
                and social_link.twitter_oauth_token_secret
            ):
                raise SocialLink.DoesNotExist()
            user = TaggUser.objects.get(id=pk)

            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_204_NO_CONTENT)

            twitter = OAuth1Session(
                settings.TWITTER_API_KEY,
                settings.TWITTER_API_SECRET,
                social_link.twitter_oauth_token,
                social_link.twitter_oauth_token_secret,
            )

            # retrieve 20 most recent tweets from twitter
            # See https://developer.twitter.com/en/docs/twitter-api/v1/tweets/timelines/api-reference/get-statuses-user_timeline
            params = {"user_id": social_link.twitter_user_id, "count": 20}
            response = twitter.get(
                "https://api.twitter.com/1.1/statuses/user_timeline.json", params=params
            )
            if response.status_code != 200:
                self.logger.error("Error retrieving Twitter posts")
                return get_response(data="Error retrieving Twitter posts", type=500)
            body = response.json()
            posts = []

            for post in body:
                post_id = post.get("id")
                screen_name = (post.get("user").get("screen_name"),)
                screen_name = screen_name[0]
                iso_date_str = datetime.strptime(
                    post.get("created_at"), "%a %b %d %H:%M:%S %z %Y"
                ).isoformat()
                profile_pic = post.get("user").get("profile_image_url_https")

                media_urls = []
                for media in post.get("extended_entities", {}).get("media") or []:
                    url = media.get("media_url_https")
                    media_urls.append(url)

                post_info = {
                    "type": "tweet",
                    "handle": screen_name,
                    "profile_pic": profile_pic,
                    "media_url": media_urls,
                    "media_type": post.get("entities", {})
                    .get("media", [{}])[0]
                    .get("type")
                    or "text",
                    "text": unescape(post.get("text")),
                    "timestamp": iso_date_str,
                    "permalink": f"https://twitter.com/{screen_name}/status/{post_id}",
                    "in_reply_to": {},
                }

                in_reply_to_id = post.get("in_reply_to_status_id")
                quoted_status_id = post.get("is_quote_status")

                if (in_reply_to_id and in_reply_to_id != "None") or (
                    quoted_status_id and quoted_status_id != "None"
                ):
                    post_info["type"] = "reply"
                    response = twitter.get(
                        f"https://api.twitter.com/1.1/statuses/show.json?id={in_reply_to_id}"
                    )

                    if quoted_status_id and quoted_status_id != "None":
                        post_info["type"] = "retweet"
                        in_reply_to_id = post.get("quoted_status_id")
                        response = twitter.get(
                            f"https://api.twitter.com/1.1/statuses/show.json?id={in_reply_to_id}"
                        )

                    media_url = (
                        post.get("entities", {})
                        .get("media", [{}])[0]
                        .get("media_url_https")
                    )

                    in_reply_to = response.json()

                    if "errors" in in_reply_to:
                        if (
                            0 in in_reply_to["errors"]
                            and "code" in in_reply_to["errors"][0]
                            and in_reply_to["errors"][0]["code"] == 144
                        ):
                            in_reply_to = {
                                "type": "tweet",
                                "text": "This tweet is unavailable",
                            }
                            post_info["in_reply_to"] = in_reply_to

                    else:
                        in_reply_to_screen_name = in_reply_to.get("user").get(
                            "screen_name"
                        )
                        in_reply_to = {
                            "type": "tweet",
                            "handle": in_reply_to_screen_name,
                            "profile_pic": in_reply_to.get("user").get(
                                "profile_image_url_https"
                            ),
                            "text": unescape(in_reply_to.get("text")),
                            "media_url": [media_url] if media_url else [],
                            "media_type": in_reply_to.get("entities", {})
                            .get("media", [{}])[0]
                            .get("type")
                            or "text",
                            "timestamp": datetime.strptime(
                                in_reply_to.get("created_at"), "%a %b %d %H:%M:%S %z %Y"
                            ).isoformat(),
                            "permalink": f"https://twitter.com/{in_reply_to_screen_name}/status/{in_reply_to_id}",
                        }
                        post_info["in_reply_to"] = in_reply_to

                posts.append(post_info)

                response = {
                    "handle": screen_name,
                    "profile_pic": profile_pic,
                    "posts": posts,
                }

            return Response(response, status=status.HTTP_200_OK)

        except SocialLink.DoesNotExist:
            return Response("Twitter not linked", status=status.HTTP_204_NO_CONTENT)
        except Exception as error:
            self.logger.exception("Unable to fetch from Twitter API")
            return get_response(data="Unable to fetch from Twitter API", type=500)
