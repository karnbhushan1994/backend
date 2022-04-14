from django.db import models

from ..models import TaggUser


class Chat(models.Model):
    user = models.OneToOneField(
        TaggUser, on_delete=models.CASCADE, primary_key=True, unique=True
    )
    chat_token = models.CharField(max_length=255, blank=True, unique=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
        ]
        unique_together = ("user", "chat_token")
