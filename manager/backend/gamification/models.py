from django.db import models
from django.template.defaultfilters import slugify
import json
import uuid

from ..models import TaggUser
from .constants import GAMIFICATION_TIER_DATA, GamificationTier


class GameProfile(models.Model):
    tagg_user = models.OneToOneField(
        TaggUser, primary_key=True, on_delete=models.CASCADE
    )
    tagg_score = models.IntegerField(default=0)
    tier = models.CharField(
        max_length=256,
        default=GAMIFICATION_TIER_DATA[GamificationTier.ONE.value]["title"],
    )
    rewards = models.CharField(max_length=1024, default=json.dumps([]))
    newRewardsReceived = models.CharField(max_length=1024, default=json.dumps([]))


class Feature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, null=False)
    slug = models.SlugField(max_length=100)
    tagg_score_price = models.IntegerField(
        default=1
    )  # tagg_score required to purchase feature
    active = models.BooleanField(default=True)
    upcoming = models.BooleanField(default=False)  # is feature upcoming

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class UserFeature(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        TaggUser, on_delete=models.CASCADE, related_name="features"
    )
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    # eligible_for_unlock_tagg_bg = models.BooleanField(default=False)
