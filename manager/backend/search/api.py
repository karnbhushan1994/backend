import logging
from ..suggested_people.models import Badge
from ..suggested_people.serializers import BadgeSerializer
from ..friends.utils import find_user_friends, get_friendship_status

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..discover.models import DiscoverCategory
from ..discover.serializers import DiscoverCategorySerializer
from ..models import TaggUser
from ..serializers import TaggUserSerializer
from random import shuffle


class SearchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaggUserSerializer

    def __init__(self, *args, **kwargs):
        super(SearchViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        """
        version ^1.12
        Handles a GET request to this endpoint.
        """
        user = request.user
        try:
            query = request.GET.get("query", "")
            if len(query) == 0:
                self.logger.error(
                    "Please enter the information for the user you're searching for."
                )
                return Response(
                    "Please enter the information for the user you're searching for.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception:
            self.logger.exception("Invalid query parameter.")
            return Response(
                "Invalid query parameter.", status=status.HTTP_400_BAD_REQUEST
            )

        if len(query) < 3:
            self.logger.error("Entered value should be greater than 2 characters")
            return Response(
                "Entered value should be greater than 2 characters",
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            """
            Look up users:
                Whose either first_name or last_name or username matches the query
                AND
                The logged in user is not blocked by the user.
            """
            user_matches = TaggUser.objects.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query),
                ~Q(blocker__blocked=request.user),
                ~Q(blocked__blocker=request.user),
                Q(taggusermeta__is_onboarded=True),
            )

            user_serialized = TaggUserSerializer(user_matches, many=True)

            response = {
                "users": user_serialized.data,
            }

            return Response(response)
        except Exception:
            self.logger.exception("Problem fetching search results")
            return Response(
                "Problem fetching search results",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def messages(self, request):
        """Handles a GET request to this endpoint."""
        """TODO: Add Pagination"""
        user = request.user
        try:
            query = request.GET.get("query", "")
            if len(query) == 0:
                self.logger.error(
                    "Please enter the information for the user you're searching for."
                )
                return Response(
                    "Please enter the information for the user you're searching for.",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception:
            self.logger.exception("Invalid query parameter.")
            return Response(
                "Invalid query parameter.", status=status.HTTP_400_BAD_REQUEST
            )

        # Keeping the limitation commented out for now in case
        # we need to do character limits in the future

        # if len(query) < 3:
        #     self.logger.error(
        #         "Entered value should be greater than 2 characters")
        #     return Response("Entered value should be greater than 2 characters", status=status.HTTP_400_BAD_REQUEST)

        try:
            """
            Look up users:
                Whose either first_name or last_name or username matches the query
                AND
                The logged in user is not blocked by the user.
            """
            user_matches = TaggUser.objects.filter(
                Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query),
                ~Q(blocker__blocked=request.user),
                Q(taggusermeta__is_onboarded=True),
            )

            suggested_users = []
            for current_user in user_matches:
                if user == current_user:
                    continue
                if get_friendship_status(current_user, user)[0] == "friends":
                    suggested_users.append(current_user)

            user_serialized = TaggUserSerializer(suggested_users, many=True)
            response = {
                "users": user_serialized.data,
            }
            return Response(response)
        except Exception:
            self.logger.exception("Problem fetching search results")
            return Response(
                "Problem fetching search results",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["get"])
    def suggested(self, request):
        """Handles a GET request to this endpoint."""
        """TODO: Add Pagination"""
        user = request.user
        try:
            """
            Look up users:
                Whose either first_name or last_name or username matches the query
                AND
                The logged in user is not blocked by the user.
            """
            user_matches = find_user_friends(user)
            list_q_set = list(user_matches)
            shuffle(list_q_set)
            user_serialized = TaggUserSerializer(list_q_set, many=True)
            response = {
                "users": user_serialized.data,
            }
            return Response(response)
        except Exception:
            self.logger.exception("Problem fetching search results")
            return Response(
                "Problem fetching search results",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class AllUsersViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(AllUsersViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        """Handles a GET request to this endpoint."""
        try:
            users = TaggUser.objects.all().values(
                "id", "username", "first_name", "last_name"
            )

            if users:
                return Response(users, status=status.HTTP_200_OK)
            self.logger.info("No results found")
            return Response("No results found", status=status.HTTP_404_NOT_FOUND)
        except Exception:
            self.logger.exception("Problem fetching search results")
            return Response(
                "Problem fetching search results",
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    serializer_class = TaggUserSerializer
