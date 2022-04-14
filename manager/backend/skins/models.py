import uuid

from django.db import models

from ..models import TaggUser


class TemplateType(models.TextChoices):
    ONE = "ONE"
    TWO = "TWO"
    THREE = "THREE"
    FOUR = "FOUR"
    FIVE = "FIVE"


class Skin(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(TaggUser, on_delete=models.CASCADE)
    template_type = models.CharField(
        max_length=64,
        choices=TemplateType.choices,
    )
    primary_color = models.CharField(max_length=15)
    secondary_color = models.CharField(max_length=15)
    bio_color_start = models.CharField(max_length=7, null=True)
    bio_color_end = models.CharField(max_length=7, null=True)
    bio_text_color = models.CharField(max_length=7, null=True)
    active = models.BooleanField(default=False)
