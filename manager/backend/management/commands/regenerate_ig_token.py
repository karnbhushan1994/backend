from django.core.management.base import BaseCommand
from ...social_linking.utils import regenerate_ig_token


class Command(BaseCommand):
    help = "Regenerate Instagram tokens for existing profiles"

    def handle(self, *args, **options):
        regenerate_ig_token()
