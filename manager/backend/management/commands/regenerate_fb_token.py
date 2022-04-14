from django.core.management.base import BaseCommand
from ...social_linking.utils import regenerate_fb_token


class Command(BaseCommand):
    help = "Regenerate Facebook tokens for existing profiles"

    def handle(self, *args, **options):
        regenerate_fb_token()
