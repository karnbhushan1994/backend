import functools
import uuid

from django.db import models
from model_utils.managers import InheritanceManager

from ..models import TaggUser


def rgetattr(obj, attr, *args):
    def _getattr(obj, attr):
        return getattr(obj, attr, *args)

    return functools.reduce(_getattr, [obj] + attr.split("."))


class WidgetType(models.TextChoices):
    VIDEO_LINK = "VIDEO_LINK"
    APPLICATION_LINK = "APPLICATION_LINK"
    GENERIC_LINK = "GENERIC_LINK"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"


class VideoLinkWidgetType(models.TextChoices):
    YOUTUBE = "YOUTUBE"
    TIKTOK = "TIKTOK"
    TWITCH = "TWITCH"
    VIMEO = "VIMEO"


class GenericLinkWidgetType(models.TextChoices):
    WEBSITE = "WEBSITE"
    ARTICLE = "ARTICLE"


class ApplicationLinkWidgetType(models.TextChoices):
    SPOTIFY = "SPOTIFY"
    SOUNDCLOUD = "SOUNDCLOUD"
    APPLE_MUSIC = "APPLE_MUSIC"
    APPLE_PODCAST = "APPLE_PODCAST"
    POSHMARK = "POSHMARK"
    DEPOP = "DEPOP"
    ETSY = "ETSY"
    SHOPIFY = "SHOPIFY"
    AMAZON = "AMAZON"
    AMAZON_AFFILIATE = "AMAZON_AFFILIATE"
    APP_STORE = "APP_STORE"


class SocialMedaiWidgetType(models.TextChoices):
    FACEBOOK = "FACEBOOK"
    INSTRGAM = "INSTAGRAM"
    TWITTER = "TWITTER"
    SNAPCHAT = "SNAPCHAT"
    TIKTOK = "TIKTOK"


class Widget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    order = models.PositiveIntegerField()
    custom_image = models.FileField(null=True, blank=True)
    edit_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=255, choices=(("lock", "Lock"), ("unlock", "Unlock")), default="lock"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    type = models.CharField(
        max_length=64,
        choices=WidgetType.choices,
    )
    objects = InheritanceManager()
    page = models.CharField(
        max_length=64,
    )


class RecentMomentWidget(Widget):
    font_color = models.CharField(max_length=7, default="#FFFFFF")
    indx = models.PositiveIntegerField(default=0)
    moment_id = models.CharField(max_length=50, null=True, blank=True)


class VideoLinkWidget(Widget):
    link_type = models.CharField(
        max_length=32,
        choices=VideoLinkWidgetType.choices,
    )
    url = models.CharField(max_length=8192)
    thumbnail_url = models.CharField(max_length=8192)
    font_color = models.CharField(max_length=7, null=True)
    background_url = models.CharField(max_length=8192, null=True)
    title = models.CharField(max_length=32)
    border_color_start = models.CharField(max_length=7, null=True)
    border_color_end = models.CharField(max_length=7, null=True)


class ApplicationLinkWidget(Widget):
    link_type = models.CharField(
        max_length=32,
        choices=ApplicationLinkWidgetType.choices,
    )
    url = models.CharField(max_length=8192)
    thumbnail_url = models.CharField(max_length=8192)
    font_color = models.CharField(max_length=7, null=True)
    title = models.CharField(max_length=32)
    background_url = models.CharField(max_length=8192, null=True)
    background_color_start = models.CharField(max_length=7, null=True)
    background_color_end = models.CharField(max_length=7, null=True)


class GenericLinkWidget(Widget):
    url = models.CharField(max_length=8192)
    link_type = models.CharField(
        max_length=32, choices=GenericLinkWidgetType.choices, null=True
    )
    title = models.CharField(max_length=32)
    font_color = models.CharField(max_length=7, null=True)
    thumbnail_url = models.CharField(max_length=8192)
    background_url = models.CharField(max_length=8192, null=True)
    border_color_start = models.CharField(max_length=7, null=True)
    border_color_end = models.CharField(max_length=7, null=True)


class RecentMomentWidget(Widget):
    font_color = models.CharField(max_length=7, default="#FFFFFF")
    indx = models.PositiveIntegerField(default=0)
    moment_id = models.CharField(max_length=50, null=True, blank=True)


class SocialMediaWidget(Widget):
    link_type = models.CharField(
        max_length=32,
        choices=SocialMedaiWidgetType.choices,
    )
    username = models.CharField(max_length=32, null=True)
    title = models.CharField(max_length=32, null=True)
    thumbnail_url = models.CharField(max_length=8192, null=True)
    font_color = models.CharField(max_length=7, null=True)
    background_url = models.CharField(max_length=8192, null=True)
    background_color_start = models.CharField(max_length=7, null=True)
    background_color_end = models.CharField(max_length=7, null=True)


class RewardCalculation(models.Model):
    taggId = models.ForeignKey(Widget, on_delete=models.CASCADE)
    userId = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    count = models.IntegerField(default=0)


class TaggBackgroundImageUnlock(models.Model):
    user = models.OneToOneField(TaggUser, on_delete=models.CASCADE)
    tagg_bg_image_unlocked = models.BooleanField(default=False, null=False)

    # Represents whether user has seen the award banner or not
    is_award_shown = models.BooleanField(default=False, null=False)


class TaggThumbnailImageUnlock(models.Model):
    user = models.OneToOneField(TaggUser, on_delete=models.CASCADE)
    tagg_thumb_image_unlocked = models.BooleanField(default=False, null=False)

    # Represents whether user has seen the award banner or not
    is_award_shown = models.BooleanField(default=False, null=False)


class TaggTitleFontColorUnlock(models.Model):
    user = models.OneToOneField(TaggUser, on_delete=models.CASCADE)
    tagg_title_font_color_unlocked = models.BooleanField(default=False, null=False)
