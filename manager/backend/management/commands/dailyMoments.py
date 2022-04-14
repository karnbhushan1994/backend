from django.core.management.base import BaseCommand
from ...moments.utils import dailyMoments


class Command(BaseCommand):
    help = "dailyMoments"

    def handle(self, *args, **options):
        dailyMoments()