from ...profile.utils import send_notification_profile_visits
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Send notification: profile viewed"

    def handle(self, *args, **options):
        send_notification_profile_visits()
