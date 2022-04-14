import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..utils import get_normalized_filter, validate_filter_type_in_request

from ...common.validator import check_is_valid_parameter
from ...models import (
    TaggUser,
)
from .models import ProfileViews
from .utils import (
    get_profile_view_distribution_graph_data,
    get_total_profile_view_count,
    record_profile_click,
)


class ProfileViewsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    queryset = ProfileViews.objects.all()
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(ProfileViewsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """
        To record clicks on a profile
        This includes user's clicks on their own profile too

        Args:
            user_id (multipart/form-data): uuid of the profile that was clicked on

        Returns: Status
        """
        try:
            data = request.POST
            if not check_is_valid_parameter("user_id", data):
                return Response("user_id is required", 400)

            if not check_is_valid_parameter("visitor_id", data):
                return Response("visitor_id is required", 400)

            if not TaggUser.objects.filter(id=data.get("user_id")).exists():
                return Response("User does not exist", 404)

            if not TaggUser.objects.filter(id=data.get("visitor_id")).exists():
                return Response("Visitor does not exist", 404)

            user = TaggUser.objects.filter(id=data.get("user_id"))[0]
            visitor = TaggUser.objects.filter(id=data.get("visitor_id"))[0]

            if user is not visitor:
                record_profile_click(user, visitor)
                return Response("Success", 201)

            else:
                return Response("user_id and visitor_id cannot be the same", 403)

        except Exception as err:
            self.logger.exception(err)
            return Response("Internal Server Error", 500)

    def list(self, request):
        """
        Function to retrieve profile view count and the view count's distribution according
        to the applied filter

        Args:
            filter_type (Raw JSON): To query taggs related analytics data
            Refer to SUPPORTED_FILTER_TYPES in analytics/common.py for list of valid inputs

        Returns:
            {
                views: int
                distribution: {
                    values: int[]
                    labels: string[]
                }
            }
        """
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return Response("A valid user id was not provided", 400)

            if not TaggUser.objects.filter(id=data.get("user_id")).exists():
                return Response("User does not exist", 404)

            user = TaggUser.objects.filter(id=data.get("user_id"))[0]

            validate_filter_type_in_request(request)
            filter_type = get_normalized_filter(request.query_params.get("filter_type"))

            total_views = get_total_profile_view_count(user, filter_type)
            distribution = get_profile_view_distribution_graph_data(user, filter_type)
            return Response(
                {"total_views": total_views, "distribution": distribution}, 200
            )

        except Exception as error:
            logging.error(error)
            return Response("Something went wrong", 500)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Function to retrieve profile view count and the view count's distribution according
        to the applied filter

        Args:
            filter_type (Raw JSON): To query taggs related analytics data
            Refer to SUPPORTED_FILTER_TYPES in analytics/common.py for list of valid inputs

        Returns:
            {
                total_views: int
            }

        """
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return Response("A valid user id was not provided", 400)

            if not TaggUser.objects.filter(id=data.get("user_id")).exists():
                return Response("User does not exist", 404)

            user = TaggUser.objects.filter(id=data.get("user_id"))[0]

            validate_filter_type_in_request(request)
            filter_type = get_normalized_filter(request.query_params.get("filter_type"))

            total_views = get_total_profile_view_count(user, filter_type)
            return Response({"total_views": total_views}, 200)

        except Exception as error:
            logging.error(error)
            return Response("Something went wrong", 500)
