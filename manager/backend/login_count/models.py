from django.db import models
from ..models import TaggUser


class LoginCount(models.Model):
    uid = models.OneToOneField(TaggUser, on_delete=models.CASCADE, primary_key=True)
    count = models.IntegerField(default=0)
    last_login = models.DateField(default=None, null=True)
