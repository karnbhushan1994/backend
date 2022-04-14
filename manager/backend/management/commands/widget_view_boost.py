from django.core.management.base import BaseCommand
from ...notifications.utils import widget_view_boost


class Command(BaseCommand):
    help = "widget_view_boost"

    def handle(self, *args, **options):
        widget_view_boost()
