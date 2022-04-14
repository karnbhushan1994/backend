from django.db import models

from ..models import TaggUser


class UserInterests(models.Model):
    user = models.OneToOneField(
        TaggUser, on_delete=models.CASCADE, primary_key=True, unique=True
    )
    interests = models.CharField(max_length=1024)
