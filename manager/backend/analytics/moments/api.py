import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ...models import TaggUser

from ...common.validator import check_is_valid_parameter

from ..utils import get_normalized_filter, validate_filter_type_in_request
from .utils import get_top_moment_by_filter, get_total_moment_view_count_by_filter


class MomentInsightsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super(MomentInsightsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        # returns top moment determined by moment score
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return Response("A valid user id was not provided", 400)

            if not TaggUser.objects.filter(id=data.get("user_id")).exists():
                return Response("User does not exist", 404)

            user = TaggUser.objects.filter(id=data.get("user_id"))[0]

            validate_filter_type_in_request(request)
            filter_type = get_normalized_filter(request.query_params.get("filter_type"))

            total_views = get_total_moment_view_count_by_filter(user, filter_type)
            top_moment = get_top_moment_by_filter(user, filter_type)
            return Response(
                {
                    "total_views": total_views,
                    "top_moment": top_moment,
                },
                200,
            )

        except Exception as error:
            logging.error(error)
            return Response("Something went wrong", 500)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return Response("A valid user id was not provided", 400)

            if not TaggUser.objects.filter(id=data.get("user_id")).exists():
                return Response("User does not exist", 404)

            user = TaggUser.objects.filter(id=data.get("user_id"))[0]

            validate_filter_type_in_request(request)
            filter_type = get_normalized_filter(request.query_params.get("filter_type"))

            total_views = get_total_moment_view_count_by_filter(user, filter_type)
            return Response({"total_views": total_views}, 200)

        except Exception as error:
            logging.error(error)
            return Response("Something went wrong", 500)
