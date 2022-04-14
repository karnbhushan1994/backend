import logging

from django.core.exceptions import ValidationError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum

from ...common.constants import NUM_ENGAGED_MOMENTS
from ...common import image_manager, validator
from ...common.validator import check_is_valid_parameter, get_response

from ...common.tagg_data_science import calculate_engagement_value
from ...moments.models import Moment, MomentEngagement
from ...moments.views.models import MomentViews
from ...moments.utils import keep_only_top_x_engaged_moment_posts
from ...moments.views.utils import record_moment_view
from ...models import TaggUser


class MomentViewsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(MomentViewsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        try:
            for key in [
                "moment_id",
                "viewer_id",
                "view_duration",
                "clicked_on_profile",
                "clicked_on_comments",
                "clicked_on_share",
            ]:
                if key not in request.data:
                    raise ValidationError({key: "This field is required."})
            moment_id = request.data.get("moment_id")
            viewer_id = request.data.get("viewer_id")
            # view_duration = int(request.data.get("view_duration"))
            # clicked_on_profile = bool(request.data.get("clicked_on_profile"))
            # clicked_on_comments = bool(request.data.get("clicked_on_comments"))
            # clicked_on_share = bool(request.data.get("clicked_on_share"))

            moment = Moment.objects.get(moment_id=moment_id)

            # mark_moment_as_viewed(request.user, moment)

            if not TaggUser.objects.filter(id=viewer_id).exists():
                return Response("Viewer not found", 404)

            viewer = TaggUser.objects.filter(id=viewer_id)[0]

            # Update moment insights
            record_moment_view(moment, viewer)

            # MomentEngagement is not being used significantly.
            # It used to be used for data science
            # TODO: Fix unique contrint issue in MomentEngagement while registering clicks
            # me, created = MomentEngagement.objects.get_or_create(
            #     user=viewer,
            #     moment=moment,
            # )

            # if created:
            #     me.save()
            # else:
            #     current_score = calculate_engagement_value(me)
            #     new_me = MomentEngagement(
            #         user=viewer,
            #         moment=moment,
            #         view_duration=view_duration,
            #         clicked_on_profile=clicked_on_profile,
            #         clicked_on_comments=clicked_on_comments,
            #         clicked_on_share=clicked_on_share,
            #     )
            #     new_score = calculate_engagement_value(new_me)
            #     if new_score > current_score:
            #         me.delete()
            #         new_me.save()

            # keep_only_top_x_engaged_moment_posts(viewer, NUM_ENGAGED_MOMENTS)

            return Response("success")

        except Moment.DoesNotExist:
            return Response("Moment does not exist", 400)
        except Exception as err:
            self.logger.exception("There was an error in viewing moment")
            return Response("There was an error in viewing moment")

# tma-2000 Moment scores are fetched and returned as coins to be displayed on the moment frontend
class MomentCoinDisplayViewSet(viewsets.ViewSet):

    def __init__(self, **kwargs):
        super(MomentCoinDisplayViewSet, self).__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):

        try:

            momentId = request.query_params.get('moment_id')
            #tma-2115 we take out moment views and take the score from those views, after that we round of the score so user see growth of 10 coins per 50 views
            moment_view_count = MomentViews.objects.filter(
                moment_viewed=momentId
            ).count()
            total_score = moment_view_count//5
            round_off = total_score - (total_score % 10)
            data = {
                "Moment_coins": round_off
                }
            return Response(data, status=200)

        except Exception as err:

            self.logger.exception("There was a problem in showing the moment coins")
            return Response("There was a problem in showing the moment coins")
