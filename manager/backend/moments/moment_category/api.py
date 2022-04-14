import datetime
import json
import logging

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ...gamification.constants import TAGG_SCORE_ALLOTMENT

from ...gamification.utils import increase_tagg_score

from ...common.constants import HOMEPAGE
from ...models import TaggUser
from ..models import Moment
from .models import MomentCategory, MomentCategoriesImage, MomentCategoryEditCount
from .utils import delete_categories, get_moment_categories
from rest_framework.decorators import action


class MomentsCategoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(MomentsCategoryViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        if "categories" not in request.data:
            raise ValidationError({"categories": "This field is required"})

        user = request.user
        categories = request.data.get("categories", [])

        # if not categories or categories[0] != HOMEPAGE:
        #     raise ValidationError(
        #         {"categories": "Homepage needs to be the first category"}
        #     )

        # all users SHOULD have a category with a HOMEPAGE,
        # but using get_or_create just in case
        mcm, _ = MomentCategory.objects.get_or_create(user_id=user)

        current_categories = json.loads(mcm.moments_category)

        # again, should have HOMEPAGE as the first element,
        # but just in case...
        if not current_categories or current_categories[0] != HOMEPAGE:
            current_categories = [HOMEPAGE]

        # figure out a list of categories that must be deleted
        categories_deleted = set(current_categories) - set(categories)

        successfully_deleted_categories = delete_categories(user, categories_deleted)

        if not successfully_deleted_categories:
            self.logger.error("Failed to delete categories")
            # ignore error here, continue...

        # Increase tagg score for creating a new moment category
        # for category in categories:
        #     if category not in current_categories:
        #         increase_tagg_score(user, TAGG_SCORE_ALLOTMENT["PAGE_CREATE"])

        if any([category not in current_categories] for category in categories):
            increase_tagg_score(user, TAGG_SCORE_ALLOTMENT["PAGE_CREATE"])

        mcm.moments_category = json.dumps(categories)
        mcm.save()
        for cat_name in json.loads(mcm.moments_category):
            try:
                MomentCategoryEditCount.objects.get(
                    cat_name=cat_name,
                    user_id=user,
                    category=mcm
                )
            except MomentCategoryEditCount.DoesNotExist:
                MomentCategoryEditCount.objects.create(
                    cat_name=cat_name,
                    user_id=user,
                    category=mcm,
                    edit_count=1
                )
        return Response("success")

    def retrieve(self, request, pk):
        try:
            user = TaggUser.objects.get(id=pk)
            categories = []
            for cat_name in get_moment_categories(user):
                dt = {"cat_name": cat_name}
                edit = MomentCategoryEditCount.objects.filter(
                    cat_name=cat_name, user_id=user
                ).values("edit_count", "status")
                if edit:
                    edit = edit[0]
                    dt.update({key: val for key, val in edit.items()})
                tag_image = MomentCategoriesImage.objects.filter(
                    cat_name=cat_name, user_id=user).values("tag_image")
                if tag_image:
                    tag_image = tag_image[0]
                    dt.update({key: val for key, val in tag_image.items()})
                categories.append(dt["cat_name"])
            return Response({"categories": categories})

        except TaggUser.DoesNotExist:
            self.logger.error("User does not exist")
            return Response("User does not exist", 400)

        except Exception as error:
            self.logger.exception(error)
            return Response("Something went wrong", 500)

    def patch(self, request, pk=None):
        try:
            user = request.user
            data = request.data

            if "old_page_name" not in data:
                return Response("old_page_name is required", 400)

            if "new_page_name" not in data:
                return Response("new_page_name is required", 400)

            old_name = data.get("old_page_name")
            new_name = data.get("new_page_name")

            # Get categories user has
            mc = MomentCategory.objects.get(user_id=user)
            page_names = json.loads((mc.moments_category))

            # Ensure old name exists in user's page names
            if old_name not in page_names:
                return Response("Page does not exist", 400)

            # Prevent user from creating duplicate page names
            if new_name in page_names:
                return Response("Page already exists", 400)

            # Replace old name with new name
            page_names = [new_name if name == old_name else name for name in page_names]
            mc.moments_category = json.dumps(page_names)
            mc.save()

            # Get user's moments with old name and change to new_page_name
            moments = Moment.objects.filter(user_id=user, moment_category=old_name)
            moments.update(moment_category=new_name)
            try:
                edit = MomentCategoryEditCount.objects.get(
                    user_id=user,
                    cat_name=old_name,
                    category=mc
                )
                if new_name:
                    edit.cat_name = new_name
                total_sec = (datetime.datetime.now() - edit.updated_on).total_seconds()
                edit.edit_count += 1
                if edit.edit_count > 2 and total_sec < (24 * 60 * 60):
                    edit.status = "unlock"
                edit.save()
            except:
                pass

            return Response("success", 200)

        except IntegrityError as ie:
            self.logger.exception(ie)
            return Response("Integrity error while saving new page name", 500)

        except ValueError as ve:
            self.logger.exception(ve)
            return Response("Value error while saving new page name", 500)

        except Exception as err:
            self.logger.exception(err)
            return Response("Internal server error while saving new page name", 500)

    @action(detail=False, methods=["post"], url_path="/image")
    def upload_image(self, request):
        if not request.data.get("tag_name", None):
            return Response("Please provide a tag name.", 400)
        if request.FILES.get("tag_image", None):
            return Response("Please provide a image for this tag.", 400)
        user = request.user
        category = MomentCategory.objects.filter(user_id=user, moments_category__in=request.data.get("tag_name"))
        if not category:
            return Response("You haven't created any category.", 400)
        category = category[0]
        try:
            image = MomentCategoriesImage.objects.get(
                cat_name=request.data.get("tag_name"),
                user_id=user,
                category=category
            )
        except:
            image = MomentCategoriesImage.objects.create(
                cat_name=request.data.get("tag_name"),
                user_id=user,
                category=category
            )
        image.tag_image = request.FILES.get("tag_image")
        image.save()
        return Response("Successfully uploading image with tag", 200)
