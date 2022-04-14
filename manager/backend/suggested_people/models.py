from django.db import models
from ..models import TaggUser


# Model to store badges a user can have
class Badge(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)


# Model to store the badges a user owns
class UserBadge(models.Model):
    user = models.ForeignKey(TaggUser, on_delete=models.CASCADE, related_name="user")
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="badge")

    class Meta:
        # To ensure that a user does not have duplicate badges
        unique_together = ("user", "badge")
        indexes = [
            models.Index(fields=["user"]),
        ]


class PeopleRecommender(models.Model):
    id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(
        TaggUser, on_delete=models.CASCADE, related_name="recipient"
    )
    recommendation = models.ForeignKey(
        TaggUser, on_delete=models.CASCADE, related_name="recommendatation"
    )
    friend_feature = models.FloatField()
    university_feature = models.FloatField()
    badge_feature = models.FloatField()
    class_year_feature = models.FloatField()
    interested_feature = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)
    dirty = models.BooleanField(default=False)

    class Meta:
        unique_together = ("recipient", "recommendation")
        indexes = [
            models.Index(fields=["id"]),
            models.Index(fields=["recipient"]),
        ]
