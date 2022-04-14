from django.db import models
from ..models import TaggUser


class HasRated(models.Model):
    uid = models.OneToOneField(TaggUser, on_delete=models.CASCADE, primary_key=True)
    hasRated = models.BooleanField(default=False)
