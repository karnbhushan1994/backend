import json
import logging

from ...common import image_manager
from ...common.constants import HOMEPAGE
from ...widget.models import Widget
from ..models import Moment
from .models import MomentCategory,MomentCategoryEditCount
from django.forms.models import model_to_dict

logger = logging.getLogger(__name__)


def create_single_moment_category(user, category):
    return MomentCategory.objects.create(
        user_id=user, moments_category=json.dumps([category])
    )


def get_moment_categories(user):
    mcm = MomentCategory.objects.filter(user_id=user).first()
    if not mcm:
        return []
    current_categories = json.loads(mcm.moments_category)
    if HOMEPAGE not in current_categories:
        current_categories.insert(0,HOMEPAGE)
        mcm.moments_category = json.dumps(list(set(current_categories)))
        mcm.save()
    return list(set(current_categories))


def get_recent_moment_on_profile(user):
    recent_moment = Moment.objects.filter(user_id=user).order_by("updated_on").first()
    if not recent_moment:
        return []
    return model_to_dict(recent_moment)


def delete_categories(user, categories):
    """Delete a list of categories for a user. Deletes s3 data and moment
    metadata.

    Args:
        user (TaggUser): the user
        categories (str[]): list of categories to delete
    returns:
        True or false depending on operation success
    """
    try:
        result_status = {"success": [], "failed": []}

        # delete category first, if successful, mark it as "success"
        # then try delete all the moments, do our best effort here
        for category in categories:
            try:
                # fetch all the data we need
                mcm = MomentCategory.objects.get(user_id=user)
                moments = Moment.objects.filter(user_id=user, moment_category=category)

                # try removing category
                user_categories = json.loads(mcm.moments_category)
                user_categories.remove(category)
                MomentCategoryEditCount.objects.filter(cat_name=category,user_id=user).delete()
                mcm.moments_category = json.dumps(user_categories)
                mcm.save()
                result_status["success"].append(category)

                # try delete all moments in this category
                for moment in moments:
                    success = image_manager.remove_from_s3(
                        moment.resource_path or moment.path_hash.split(".com")[1]
                    )
                    if not success:
                        # ignore the failure here and keep metadata
                        continue
                    moment.delete()

            except ValueError:
                # this happens when the category doesn't exist
                result_status["success"].append(category)
            except Exception as error:
                logger.error(f"Failed to delete moment category: {category}")
                result_status["failed"].append([category, "something went wrong"])
        return len(result_status["failed"]) == 0
    except Exception as error:
        logger.exception(error)
        return False
