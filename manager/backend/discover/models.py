from django.db import models


class DiscoverCategory(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=128, unique=True)
    category = models.CharField(max_length=128, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["id"]),
        ]
