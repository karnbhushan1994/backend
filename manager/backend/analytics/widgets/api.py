import logging

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ...models import TaggUser

from ...common.exception_handling.exception_classes import MissingParameterException
from ...common.validator import FieldException, check_is_valid_parameter
from ..utils import (
    get_normalized_filter,
    validate_filter_type_in_request,
)
from .utils import (
    get_top_widget,
    get_total_widget_view_count,
    get_widget_view_distribution_by_widget,
    record_widget_click,
)
from .models import Widget, WidgetViews
from .serializers import WidgetViewsSerializer


class WidgetViewsViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    queryset = WidgetViews.objects.all()
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(WidgetViewsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """
        To record clicks on a tagg
        This includes user's clicks on their own widgets too

        Args:
            widget_id (Raw JSON): uuid of the widget that was clicked on

        Returns: Status
        """
        try:
            data = request.data

            if "widget_id" not in request.data:
                return Response("widget_id required", 400)

            if "viewer_id" not in request.data:
                return Response("viewer_id required", 400)

            if not TaggUser.objects.filter(id=data.get("viewer_id")).exists():
                return Response("Viewer does not exist", 404)

            viewer = TaggUser.objects.filter(id=data.get("viewer_id"))[0]

            if Widget.objects.filter(
                active=True, id=request.data.get("widget_id")
            ).exists():
                widget = Widget.objects.filter(
                    active=True, id=request.data.get("widget_id")
                )[0]
                record_widget_click(widget, viewer)

            else:
                return Response("Widget does not exist", 403)

            return Response("Success", 201)

        except Exception as err:
            self.logger.exception(err)
            return Response("Internal Server Error", 500)

    def list(self, request):
        """
        To retrieve detailed taggs related analytics data by filter_type, as follows:
            1. Total click count
            2. Distribution of these clicks among user's taggs

        Args:
            filter_type (Raw JSON): To query taggs related analytics data
            Refer to SUPPORTED_FILTER_TYPES in analytics/common.py for list of valid inputs

        Returns:
            {
                total: int
                individual: [
                    {
                        "link_type": subtype of widget,
                        "title": title/page_name/username depending on the type of widget,
                        "views": int,
                    }
                ]
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

            total_views = get_total_widget_view_count(user, filter_type)
            view_distribution = get_widget_view_distribution_by_widget(
                user, filter_type
            )

            view_distribution_serialized = WidgetViewsSerializer(
                view_distribution, many=True
            ).data
            return Response(
                {
                    "total": total_views,
                    "individual": view_distribution_serialized,
                },
                200,
            )

        except MissingParameterException as err:
            self.logger.exception("Missing required paramerts: filter_type ", err)
            return Response("Missing required paramerts: filter_type", 400)

        except FieldException as err:
            self.logger.exception("Unsupported filter type", err)
            return Response(
                "Unsupported filter type, supported filters: 7, 14, 30, LIFETIME", 403
            )

        except Exception as error:
            self.logger.exception(error)
            return Response(
                "There was a problem whle fetching the taggs clicks data", 500
            )

    @action(detail=False, methods=["GET"])
    def summary(self, request):
        """
        To retrieve a jist of taggs related analytics data by filter_type, as follows:
            1. Total click count
            2. Tagg with the maximum clicks

        Args:
            filter_type (Raw JSON): To query taggs related analytics data
            Refer to SUPPORTED_FILTER_TYPES in analytics/common.py for list of valid inputs

        Returns:
            {
                total: int
                "top_tagg": {
                        "link_type": subtype of widget,
                        "title": title/page_name/username depending on the type of widget,
                        "views": int,
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

            total_views = get_total_widget_view_count(user, filter_type)
            top_tagg = get_top_widget(user, filter_type)

            top_tagg_serialized = WidgetViewsSerializer(top_tagg).data
            return Response(
                {"total": total_views, "top_tagg": top_tagg_serialized}, 200
            )

        except MissingParameterException as err:
            self.logger.exception("Missing required paramerts: filter_type ", err)
            return Response("Missing required paramerts: filter_type", 400)

        except FieldException as err:
            self.logger.exception("Unsupported filter type", err)
            return Response(
                "Unsupported filter type, supported filters: 7, 14, 30, LIFETIME", 403
            )

        except Exception as err:
            self.logger.exception(
                "There was a problem whle fetching the taggs click summary"
            )
            return Response(
                "There was a problem whle fetching the taggs click summary", 500
            )
