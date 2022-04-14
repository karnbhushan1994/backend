import logging
from django.db.models.query_utils import Q
from django.utils import timezone
from enum import Enum

import requests
from django.conf import settings

from ..models import TaggUser
from .models import SocialLink

Socials = Enum("Socials", "Snapchat TikTok")

Social_URLs = {
    Socials.Snapchat: lambda usr: f"https://www.snapchat.com/add/{usr}",
    Socials.TikTok: lambda usr: f"https://www.tiktok.com/@{usr}",
}


def regenerate_ig_token(users=[]):
    """
    For each row we try to refresh:
     1. If there's a token date, do nothing if it's not about to expire
     2. Else try to refresh token...
        - Success: Update old token with new one, update token date
        - Failed : Remove IG link completely
            - possibility 1: token already expired
            - possibility 2: account is private, unable to renew
    """
    logger = logging.getLogger("regenerate_socials")
    logger.info("Started")

    if users:
        for user in users:
            # not checking for token age, force regenerate
            social_link = SocialLink.objects.get(user_id=user)
            _regenerate_ig_token(social_link)
    else:
        for link in SocialLink.objects.filter(~Q(ig_user_id="")):
            # Step 1
            if link.ig_token_date:
                diff = timezone.now() - link.ig_token_date
                if diff.days < 55:
                    logger.info(
                        f"{str(link.id).ljust(3)} - {link.user_id.username.ljust(20)}: IG - {60 - diff.days} days till expired, do nothing"
                    )
                    continue
            # Step 2
            _regenerate_ig_token(link, logger)
    logger.info("Done")


def regenerate_fb_token(users=[]):
    """
    if users is not empty, we force regenerate token for all users
    if users is empty, we check for all TaggUsers and regenerate based on token age
    """
    logger = logging.getLogger("regenerate_socials")
    logger.info("Started")

    if users:
        for user in users:
            # not checking for token age, force regenerate
            social_link = SocialLink.objects.get(user_id=user)
            _regenerate_fb_token(social_link)
    else:
        for user in TaggUser.objects.all():
            # check for token age if it's 58 < token_age < 60 days
            social_link = SocialLink.objects.get(user_id=user)
            token_date = social_link.fb_token_date
            if not token_date:
                return
            diff = timezone.now() - token_date
            if 58 <= diff.days < 60:
                _regenerate_fb_token(social_link, logger)
            # TODO: make sure the token is actually not working before we decide to remove it
            # elif diff.days > 60:
            #     social_link.fb_user_id = ''
            #     social_link.fb_access_token = ''
            #     social_link.fb_token_date =''


def _regenerate_fb_token(social_link, logger):
    """
    regenerate token for the user's social link
    """
    try:
        token = social_link.fb_access_token

        if not token:
            logger.error("Empty user Facebook token")
            return

        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "access_token": token,
        }

        response = requests.get(
            "https://graph.facebook.com/v8.0/oauth/client_code", params=params
        )
        if response.status_code // 100 != 2:
            logger.info(response.json())
            logger.error("Unable to regenerate Facebook token with the first FB API")
            return

        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "code": response.json()["code"],
        }

        response = requests.get(
            "https://graph.facebook.com/v8.0/oauth/access_token", params=params
        )

        if response.status_code // 100 != 2:
            logger.error("Unable to regenerate Facebook token with the second FB API")
            return

        new_long_lived_token = response.json()["access_token"]

        social_link.fb_access_token = new_long_lived_token
        social_link.fb_token_date = timezone.now()
        social_link.save()

        logger.info(
            f"Regenerated token for user: {social_link.user_id.username.ljust(20)}"
        )

    except Exception as error:
        logger.exception(error)
        return


def _regenerate_ig_token(link, logger):
    link_id_debug = str(link.id).ljust(3)
    username_debug = link.user_id.username.ljust(20)
    try:
        params = {
            "grant_type": "ig_refresh_token",
            "access_token": link.ig_access_token,
        }
        response = requests.get(
            "https://graph.instagram.com/refresh_access_token", params=params
        )
        if response.status_code // 100 == 2:
            new_token = response.json()["access_token"]
            link.ig_access_token = new_token
            link.ig_token_date = timezone.now()
            logger.info(
                f"{link_id_debug} - {username_debug}: IG - Successfully refreshed token"
            )
        else:
            body = response.json()
            error_code = int(body["error"]["code"])
            link.ig_access_token = ""
            link.ig_user_id = ""
            link.ig_token_date = None
            if error_code == 190:
                logger.info(
                    f"{link_id_debug} - {username_debug}: IG - Removing link, failed to refresh token (token invalidated/expired)"
                )
            elif error_code == 10:
                logger.info(
                    f"{link_id_debug} - {username_debug}: IG - Removing link, failed to refresh token (not expired, just unable to refresh for a private account)"
                )
            else:
                logger.info(
                    f"{link_id_debug} - {username_debug}: IG - Removing link, failed to refresh token (not sure why, see below)"
                )
                logger.error(body)
        link.save()
    except Exception as error:
        logger.exception(error)
        logger.error(f"{link_id_debug} - {username_debug}: IG - Something went wrong")


def get_linked_socials(user):
    linked_socials = []
    social_link, social_link_created = SocialLink.objects.get_or_create(user_id=user)
    if social_link.fb_user_id:
        linked_socials.append("Facebook")
    if social_link.ig_user_id:
        linked_socials.append("Instagram")
    if social_link.twitter_user_id:
        linked_socials.append("Twitter")
    if social_link.snapchat_username:
        linked_socials.append("Snapchat")
    if social_link.tiktok_username:
        linked_socials.append("TikTok")
    return linked_socials
