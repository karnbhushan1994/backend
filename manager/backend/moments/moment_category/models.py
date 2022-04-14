from django.db import models

from ...models import TaggUser
import datetime


class MomentCategory(models.Model):
    user_id = models.OneToOneField(TaggUser, on_delete=models.CASCADE, primary_key=True, related_name="momentcategory")
    moments_category = models.CharField(max_length=1024)


class MomentCategoryEditCount(models.Model):
    cat_name = models.CharField(max_length=255)
    user_id = models.ForeignKey(TaggUser, on_delete=models.CASCADE, related_name="edits")
    category = models.ForeignKey(MomentCategory, on_delete=models.CASCADE, related_name="edits")
    edit_count = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=255, choices=(("lock", "Lock"), ("unlock", "Unlock")), default="lock")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        self.updated_on = datetime.datetime.now()
        super().save(*args, **kwargs)


class MomentCategoriesImage(models.Model):
    tag_image = models.FileField(null=True, upload_to="cat_image")
    cat_name = models.CharField(max_length=255)
    user_id = models.ForeignKey(TaggUser, on_delete=models.CASCADE, related_name="tag_image")
    category = models.ForeignKey(MomentCategory, on_delete=models.CASCADE, related_name="tag_image")
    created_on = models.DateTimeField(auto_now_add=True)
