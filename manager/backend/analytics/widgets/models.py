from django.db import models

from ...widget.models import Widget
from ...models import TaggUser


class WidgetViews(models.Model):
    widget = models.ForeignKey(
        Widget, related_name="widget", on_delete=models.SET_NULL, null=True
    )
    viewer = models.ForeignKey(
        TaggUser, related_name="widget_viewer", on_delete=models.SET_NULL, null=True
    )
    timestamp = models.DateTimeField(auto_now_add=True)
