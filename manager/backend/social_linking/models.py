from django.db import models

from ..models import TaggUser


class SocialLink(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.OneToOneField(TaggUser, on_delete=models.CASCADE)
    fb_user_id = models.CharField(max_length=128)
    fb_access_token = models.CharField(max_length=256)
    fb_token_date = models.DateTimeField(blank=True, null=True)
    ig_user_id = models.CharField(max_length=128)
    ig_access_token = models.CharField(max_length=256)
    ig_token_date = models.DateTimeField(blank=True, null=True)
    twitter_oauth_token = models.CharField(max_length=64, default="")
    twitter_oauth_token_secret = models.CharField(max_length=64, default="")
    twitter_user_id = models.CharField(max_length=64, default="")
    twitter_screen_name = models.CharField(max_length=64, default="")
    snapchat_username = models.CharField(max_length=256, default="")
    tiktok_username = models.CharField(max_length=256, default="")
