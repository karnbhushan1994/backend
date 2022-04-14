from ...suggested_people.utils import (
    compute_recommender_feature_values,
    insert_recommender_missing_rows,
)
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Populate missing rows and recommender feature values"

    def handle(self, *args, **options):
        insert_recommender_missing_rows()
        compute_recommender_feature_values()
