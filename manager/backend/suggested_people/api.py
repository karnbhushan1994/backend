import json
import logging

from django.core.cache import cache
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..common.image_manager import Image, ImageUploadException, settings, upload_image
from ..common.image_validator import check_image_ratio
from ..common.validator import check_is_valid_parameter, get_response
from ..models import SuggestedPeopleLinked, TaggUser
from ..serializers import TaggUserSerializer
from .models import Badge, UserBadge
from .paginators import SuggestedPeoplePaginator
from .serializers import SuggestedPeopleSerializer
from .utils import (
    get_image_and_file_name,
    get_mutual_friends,
    get_suggested_people,
    mark_user_dirty,
    mark_users_uninterested_1_count,
)


class SuggestedPeopleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = SuggestedPeoplePaginator

    def __init__(self, *args, **kwargs):
        super(SuggestedPeopleViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk):
        """
        Endpoint to return a single "Suggested Person" for a requested user.
        """
        try:
            user = TaggUser.objects.get(id=pk)
            serialized = SuggestedPeopleSerializer(user, context={"user": request.user})
            return get_response(serialized.data, type=200)
        except Exception as error:
            self.logger.error(error)
            return get_response("Something went wrong", type=500)

    def list(self, request):
        """
        Endpoint to return suggested people for the logged in user
        Right now just use the concept of non_friends on Tagg to get the list of suggested people
        Optionally takes in a filter named badge, to filter suggested_people by badge name the user is associated with
        """
        try:
            user = request.user
            params = request.query_params
            offset = int(params.get("offset", -1))
            limit = int(params.get("limit", -1))
            seed = params.get("seed", 0)

            cache_time = 600

            sp_cache_key = f"sp_{user.id}_{seed}"

            suggested_people = cache.get(sp_cache_key)

            if not suggested_people:
                suggested_people = get_suggested_people(user, seed)
                cache.set(sp_cache_key, suggested_people, cache_time)

            if offset != -1 and limit != -1:
                mark_users_uninterested_1_count(
                    str(user.id),
                    [str(u.id) for u in suggested_people[offset : offset + limit]],
                )

            suggested_people = self.paginate_queryset(suggested_people)

            serialized_response = SuggestedPeopleSerializer(
                suggested_people, many=True, context={"user": user}
            ).data

            return self.get_paginated_response(serialized_response)
        except Exception as error:
            self.logger.error(error)
            return get_response("Problem occurred", type=500)

    @action(detail=False, methods=["post"])
    def update_picture(self, request):
        """
        Takes the picture to be uploaded as part of user's suggested people page and uploads the same to s3
        Picture uploaded would sit on the url : https://{bucket-name}.s3.us-east-2.amazonaws.com/suggestedPeople/sdp-{user-id}.{image-extension}
        Args :
            image : image object
        Returns :
            http response code
        """
        try:
            user = request.user
            if not request.FILES or "suggested_people" not in request.FILES:
                self.logger.error("Image not provided")
                return get_response("Image not provided", type=400)
            image = Image.open(request.FILES["suggested_people"])

            if not check_image_ratio(image, settings.SP_RATIO, tolerance=0.1):
                self.logger.error("Image dimensions are invalid")

                # Return 401 so the error can be caught and user can be notified explicitly about the same.
                return get_response("Image dimensions are invalid", type=401)
            image_name, filename = get_image_and_file_name(user.id)
            upload_image(image, filename, image_name)

            # Check if user is onboarding suggested people or simple updating an existing link
            if (
                user.taggusermeta.suggested_people_linked
                == SuggestedPeopleLinked.FINAL_TUTORIAL
            ):
                pass
            else:
                user.taggusermeta.suggested_people_linked = (
                    SuggestedPeopleLinked.PICTURE_UPLOADED
                )

            user.save()
            return get_response("Success", type=201)
        except ImageUploadException:
            self.logger.exception("Failed to upload image")
            return get_response("Failed to upload image", type=500)
        except Exception as error:
            self.logger.exception("Something unexpected happened", type=500)
            return get_response("Something unexpected happened", type=500)

    @action(detail=False, methods=["post"])
    def add_badges(self, request):
        """
        Given a user, and a list of badges, adds badges for the user.
        Args:
            badges: list of badge names
        Returns:
            http response status
        NOTE:
            Skipping check for duplicate badges and hoping that the user interface will take care of
        """
        try:
            user = request.user
            data = request.POST
            if not check_is_valid_parameter("badges", data):
                self.logger.error("Badges are required")
                return get_response("Badges are required", type=400)
            badges = json.loads(data["badges"])

            # Maximum number of badges allowed is 3
            if (
                UserBadge.objects.filter(user=user).count() + len(badges)
                > settings.BADGE_LIMIT
            ):
                self.logger.error("User may not have more than 3 badges")
                return get_response("User may not have more than 3 badges", type=400)

            badge_objects = Badge.objects.filter(name__in=badges)

            # Name of badges provide should match exactly (name and case wise) with badges existing in Tagg's database
            # Short circuit if any of the badges do not exist for the university, the user is enrolled to
            if badge_objects.count() != len(badges):
                self.logger.error("Some of the badges provided are invalid")
                return get_response("Some of the badges provided are invalid", type=401)

            for badge in badge_objects:
                object = UserBadge.objects.create(user=user, badge=badge)
                object.save()
            mark_user_dirty(str(user.id))
            return get_response("Success", type=201)
        except Exception as error:
            self.logger.exception("Error adding badges")
            return get_response("Error adding badges", type=500)

    @action(detail=False, methods=["post"])
    def update_badges(self, request):
        """
        Given a list of new badges, replace them with the current user badges.
        Args:
            badges: list of badge names
        Returns:
            http response status
        """
        try:
            data = request.POST
            if not check_is_valid_parameter("badges", data):
                return Response("badges is required", 400)

            badges = json.loads(data["badges"])

            if len(badges) > settings.BADGE_LIMIT:
                self.logger.error("User may not have more than 3 badges")
                return get_response("User may not have more than 3 badges", type=400)
            badge_objects = Badge.objects.filter(name__in=badges)
            if len(badge_objects) != len(badges):
                self.logger.error("Some of the badges provided are invalid")
                return get_response("Some of the badges provided are invalid", type=401)
            # remove all current user badges
            for o in UserBadge.objects.filter(user=request.user):
                o.delete()
            # add all new badges
            for bo in badge_objects:
                UserBadge.objects.create(user=request.user, badge=bo)
            mark_user_dirty(str(request.user.id))
            return Response("Success")
        except Exception as error:
            self.logger.exception(error)
            return get_response("Something went wrong", type=500)

    @action(detail=False, methods=["get"])
    def get_mutual_badge_holders(self, request):
        """
        Given a badge id, retrieve list of users holding the same badge id
        Args:
            badge_id: string
        Returns:
           list of users of the format:
           {
               id,
               username,
               firstname,
               lastname,
               thumbnail_url,
           }
        """
        try:
            data = request.query_params

            if not check_is_valid_parameter("badge_id", data):
                self.logger.error("badge_id is required")
                return get_response("badge_id is required", type=404)

            badge_id = data.get("badge_id")
            badge_holder_ids = UserBadge.objects.filter(
                Q(badge_id=badge_id), ~Q(user_id=request.user.id)
            ).values("user_id")
            badge_holders = TaggUser.objects.filter(Q(id__in=badge_holder_ids))

            return get_response(
                TaggUserSerializer(badge_holders, many=True).data, type=200
            )
        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user id")
            return get_response("Invalid user id", type=404)
        except Exception as error:
            self.logger.exception("Error retrieving badges")
            return get_response("Error retrieving badges", type=500)

    @action(detail=False, methods=["delete"])
    def remove_badges(self, request):
        """
        Given a user, and a list of badges, deletes badges for the user.
        Args:
            None
        Returns:
            http response status
        NOTE : Relying on the user interface to send in the right badge names
        """
        try:
            user = request.user
            data = request.POST
            if not check_is_valid_parameter("badges", data):
                self.logger.error("Badges are required")
                return get_response("Badges are required", type=400)
            badges = json.loads(data["badges"])

            for badge in badges:
                UserBadge.objects.filter(user=user, badge__name=badge).first().delete()
            mark_user_dirty(str(user.id))
            return get_response("Success", type=200)
        except Exception as error:
            self.logger.exception("Error deleting badges")
            return get_response("Error deleting badges", type=500)

    @action(detail=False, methods=["get"])
    def get_mutual_friends(self, request):
        """
        Given a user_id, retrieve list of mutual_friends between this user and the requesting user
        Args:
            user_id: string
        Returns:
           list of TaggUser objects:
           {
             id: 'string'
             first_name: 'string',
             last_name: 'string',
             username: 'string',
             thumbnail_url: 'string'
           }
        """
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                self.logger.error("user_id is required")
                return get_response("user_id is required", type=404)
            user1 = request.user
            user2 = TaggUser.objects.filter(id=data.get("user_id")).first()
            friends = get_mutual_friends(user1, user2)
            friends = TaggUserSerializer(friends, many=True).data
            return get_response(friends, type=200)
        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user id")
            return get_response("Invalid user id", type=404)
        except Exception as error:
            self.logger.exception("Error retrieving mutual friends")
            return get_response("Error retrieving mutual friends", type=500)
