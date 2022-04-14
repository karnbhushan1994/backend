import logging
import random

from django.conf import settings
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..serializers import TaggUserSerializer
from ..suggested_people.models import Badge, UserBadge
from ..suggested_people.serializers import BadgeSerializer
from .models import DiscoverCategory
from .serializers import BadgeToDiscoverCategorySerializer, DiscoverCategorySerializer
from .utils import discover_query


class DiscoverViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(DiscoverViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk):
        """
        Return all users belong to a certain category given a pk

        ```
        {
            "title": "Trending on Tagg",
            "users": [...]
        }
        ```
        """
        try:
            # "discover" or "badge", defaults to "discover"
            category_type = request.query_params.get("type", "discover")

            if category_type == "badge":
                title = Badge.objects.get(id=pk).name
                users = [ub.user for ub in UserBadge.objects.filter(badge_id=pk)]
                response = {
                    "title": title,
                    "users": TaggUserSerializer(users, many=True).data,
                }
            else:
                category = DiscoverCategory.objects.get(id=pk)
                users = discover_query(category.name)(request.user)
                response = {
                    "title": category.name,
                    "users": TaggUserSerializer(users, many=True).data,
                }

            return Response(response)

        except DiscoverCategory.DoesNotExist:
            return Response("Category not found", status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            self.logger.error(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def list(self, request):
        """
        Returns current discover/badge categories.

        ```
        {
            "categories": [
                {
                    "id": 1,
                    "name": "Trending on Tagg",
                    "category": "Brown", // null or "Brown" atm
                },
                ...
            ],
            "badges": [
                {
                    "id": 1,
                    "name": "Art",
                },
                ...
            ]
        }
        ```
        """
        try:
            return Response(
                {
                    "categories": DiscoverCategorySerializer(
                        DiscoverCategory.objects.all(), many=True
                    ).data,
                    "badges": BadgeSerializer(Badge.objects.all(), many=True).data,
                }
            )
        except Exception as error:
            self.logger.error(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def all(self, request):
        """
        (Legacy) Returns all categories and all of its users.

        ```
        {
            "categories":
                "new_to_tagg": [...],
                "people_you_may_know": [...],
        }
        ```
        """
        try:
            user = request.user
            response = {"categories": {}}

            for category_key in settings.DISCOVER_CATEGORIES:
                response["categories"][category_key] = TaggUserSerializer(
                    discover_query(category_key)(user), many=True
                ).data

            return Response(response)
        except Exception as error:
            self.logger.error(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def get_users(self, request):
        """
        Returns a list of users based on the given badge/discover category name.
        """
        try:
            category_name = request.query_params.get("category", None)
            if not category_name:
                self.logger.error("category is required")
                return Response(
                    "category is required", status=status.HTTP_400_BAD_REQUEST
                )
            o = DiscoverCategory.objects.filter(name=category_name)
            if o:
                response = TaggUserSerializer(
                    discover_query(category_name)(request.user), many=True
                ).data
                return Response(response)
            o = Badge.objects.filter(name=category_name)
            if o:
                users = [
                    ub.user
                    for ub in UserBadge.objects.filter(
                        badge__name=category_name,
                    )
                ]
                response = TaggUserSerializer(users, many=True).data
                return Response(response)
            return Response("No category found", status=status.HTTP_404_NOT_FOUND)
        except Exception as error:
            self.logger.error(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def search_buttons(self, request):
        """
        Return random 4 categories (2 each from badge/discover categories).
        serialized data to have consistent type on the Frontend.
        NOTE: we will be returning a Badge as a DiscoverCategory

        ```
        [
            {
                id: '',
                name: '',
                category: '',
            },
            ...
            {
                id: '', # badge id is incremented by 100000
                name: '',
                category: "Badge",
            },
            ...
        ]
        ```
        """
        user = request.user
        try:
            dcs = DiscoverCategory.objects.filter(
                category=user.university.split(" ")[0]
            ).order_by("?")[:2]
            ubs = Badge.objects.all().order_by("?")[:2]

            dcs_serialized = DiscoverCategorySerializer(dcs, many=True).data
            ubs_serialized = BadgeToDiscoverCategorySerializer(ubs, many=True).data

            response = dcs_serialized + ubs_serialized
            random.shuffle(response)

            return Response(response)
        except Exception as error:
            self.logger.error(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
