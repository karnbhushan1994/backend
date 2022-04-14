from django.core.management.base import BaseCommand
from ...notifications.utils import link_taggs_reminder


class Command(BaseCommand):
    help = "Send reminders for linking taggs"

    def handle(self, *args, **options):
        link_taggs_reminder()
