import logging
import random

from django.core.exceptions import ValidationError
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from ..models import TaggUser
from ..moments.comments.models import MomentComments
from ..moments.models import Moment
from ..moments.moment_category.utils import get_moment_categories
from ..skins.models import Skin
from ..widget.models import Widget
from ..widget.serializers import WidgetSerializer
from .serializers import (
    WebMomentPostSerializer,
    WebUserProfileSerializer,
    WebUserSerializer,
)


class WebViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    @swagger_auto_schema(
        method="get",
        manual_parameters=[
            openapi.Parameter("username", openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ],
    )
    @action(detail=False, methods=["get"])
    def profile(self, request):
        try:
            if "username" not in request.GET:
                raise ValidationError({"username": "This field is required."})
            user = TaggUser.objects.get(username=request.GET.get("username"))
            return Response(WebUserProfileSerializer(user).data)
        except TaggUser.DoesNotExist:
            return Response("User does not exist", 400)
        except Skin.DoesNotExist:
            # a user should always have an active skin
            return Response("Something went wrong", 500)

    @swagger_auto_schema(
        method="get",
        manual_parameters=[
            openapi.Parameter("username", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("page", openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
    )
    @action(detail=False, methods=["get"])
    def page(self, request):
        try:
            for key in ["username", "page"]:
                if key not in request.GET:
                    raise ValidationError({key: "This field is required."})
            user = TaggUser.objects.get(username=request.GET.get("username"))
            page = request.GET["page"]
            # if page not in get_moment_categories(user):
                # raise ValidationError({"page": "User does not have that page name."})
            return Response(
                {
                    "page": page,
                    "widgets": WidgetSerializer(
                        Widget.objects.filter(owner=user, page=page, active=True)
                        .order_by("order")
                        .select_subclasses(),
                        many=True,
                    ).data,
                    "moments": WebMomentPostSerializer(
                        Moment.objects.filter(
                            user_id=user, moment_category=page
                        ).order_by("-date_created"),
                        many=True,
                    ).data,
                }
            )
        except TaggUser.DoesNotExist:
            return Response("User does not exist", 400)

    @action(detail=False, methods=["get"])
    def top_profiles(self, request):
        """
        Returns a randmized list of top 25 percentile of tagg users
        according to their Tagg Score. 16 at a time.
        """
        # TODO: Tagg Score isn't implemented yet, will calculate based on last login
        return Response(
            WebUserSerializer(
                TaggUser.objects.filter(last_login__isnull=False)
                .order_by("-last_login")
                .distinct()[:16],
                many=True,
            ).data
        )

    @action(detail=False, methods=["get"])
    def discover_moments(self, request):
        # TODO: tmp work, we should be hitting DS for this
        # but doing some simple query for now.
        comments = MomentComments.objects.all()
        # first three moments will have a comment
        moments_with_comment = list(set([c.moment_id for c in comments]))[:3]
        # last two comments will likely not have a comment
        # (most moments don't have any comments)
        recent_moments = list(Moment.objects.all().order_by("-date_created")[:2])

        moments = moments_with_comment + recent_moments

        return Response(WebMomentPostSerializer(moments, many=True).data)
