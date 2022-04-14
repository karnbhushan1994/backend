from django.core.management.base import BaseCommand
from ...notifications.utils import moment_posted_friend


class Command(BaseCommand):
    help = "Send notification for moment posted by a friend"

    def handle(self, *args, **options):
        moment_posted_friend()
