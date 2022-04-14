from django.core.management.base import BaseCommand
from ...notifications.utils import moments_posted_reminder


class Command(BaseCommand):
    help = "Send notification for moments posted"

    def handle(self, *args, **options):
        moments_posted_reminder()
