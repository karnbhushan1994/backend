from django.db import models
from ...models import TaggUser


class ProfileViews(models.Model):
    profile_visited = models.ForeignKey(
        TaggUser, on_delete=models.CASCADE, related_name="visited"
    )
    profile_visitor = models.ForeignKey(
        TaggUser, on_delete=models.SET_NULL, null=True, related_name="visitor"
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["profile_visited", "timestamp"])]


# TODO: Remove table after March 1, 2022,
# Not used anywhere except in ProfileViewsViewSet, so it must be removed after March 1, 2022,
# since all the views will be used from ProfileViews table
# ProfileVisits is not recording any new views and we suport a max of 30 day filter on the frontend
# Moreover, after the sending the notification, we were clearing this table out, so it has no significant data
class ProfileVisits(models.Model):
    user = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    visitors = models.CharField(max_length=1024, blank=True)

    class Meta:
        indexes = [models.Index(fields=["user"])]
