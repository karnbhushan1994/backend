import json
import logging
import os
from datetime import datetime, timedelta
from pickle import OBJ
from twilio.rest import Client
import boto3
import pytz
import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.http.response import HttpResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from ..common.image_manager import profile_pic_url
from ..common import image_manager, validator
from ..common.utils import permission_by_action
from ..common.validator import check_is_valid_parameter, get_response
from ..gamification.constants import TAGG_SCORE_ALLOTMENT
from ..gamification.models import GameProfile
from ..gamification.utils import (
    TaggScoreUpdateException,
    increase_tagg_score,
    decrease_tagg_score,
    has_enough_tagg_score,
)
from ..models import DMViewStage, TaggUser, TaggUserMeta,InvitedUser
from ..notifications.utils import notify_mentioned_users
from ..profile.utils import allow_to_view_private_content
from .models import DailyMoment, Moment
from .moment_category.models import MomentCategory
from .paginators import DiscoverMomentsPaginator
from .serializers import (
    MomentPostSerializer,
    MomentSerializer,
    PublicMomentPostSerializer,
)
from .tags.models import MomentTagList
from operator import itemgetter
from .tags.serializers import MomentTagSerializer
from .tags.utils import replace_tags
from .utils import (
    get_pre_path,
    get_pre_s3_uri,
    get_thumbnail_url,
    get_user_moments,
    suggest_moments_naive,
)
from .views.models import MomentViews
from ..widget.models import Widget


@permission_by_action
class MomentsViewSet(viewsets.ViewSet):
    permission_classes_by_action = {
        "default": [IsAuthenticated],
        "retrieve": [AllowAny],
    }
    serializer_class = MomentSerializer

    def __init__(self, *args, **kwargs):
        super(MomentsViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """Upload images in an asynchronous manner and update the Moment model

        Args:
            multiple images = (file) Files to be uploaded:
            moment = (str) Moment category
            captions = (dict) Caption for each image {image_name : caption}

        Returns:
            dict {image_name : upload_status} :
        """
        data = request.POST
        if not check_is_valid_parameter("moment", data):
            return validator.get_response(data="moment is required", type=400)

        if not check_is_valid_parameter("captions", data):
            return validator.get_response(data="captions is required", type=400)

        images = request.FILES
        metadata = None

        if not images:
            return validator.get_response(
                data="No images were found to be uploaded", type=400
            )

        user = request.user
        user_id = request.user.id
        moment = data.get("moment")
        captions = json.loads(data.get("captions"))

        # Check if user has enough coins to create moment
        if not has_enough_tagg_score(user, TAGG_SCORE_ALLOTMENT["MOMENT_POST"]):
            return Response("Not sufficient tagg score to post moment", status=400)

        try:
            """
            Image Upload Algorithm :
            1 - Construct a list of lists of size - number of images : Each list contains a tuple of 3 parameter to be passed to upload_image_async (image_name, the actual image, filename).
            2 - While constructing the list, hash the image path and keep a track of that.
            3 - Try uploading each image asynchronously. Failure to upload one image should not affect another image.
            4 - Return a list of {image_name : upload_status} as response.
            5 - For all the successful image uploads, update the Moment model (time of upload is determined on the backend)
            """
            moments = []
            hashes = {}

            # Retrieve the caption if there exists one for the given image
            def get_caption(image_name):
                return captions[image_name] if image_name in captions else ""

            hashes = image_manager.generate_s3_image_filepaths(
                images, get_pre_path(user_id, moment)
            )

            for image_name, image_content in images.items():
                moments.append((image_name, image_content, hashes[image_name]))

            image_upload_status = image_manager.upload_images_async(
                moments, upload_thumbnail=True
            )
            data = {
                "moments": image_upload_status,
            }
            s3_pre_uri = get_pre_s3_uri(
                image_manager.settings.S3_BUCKET,
                image_manager.settings.S3_PRE_OBJECT_URI,
            )
            # Save details of all the images that were stored successfully in the local database (Moment)
            for image_name, image_content in images.items():
                if image_upload_status[image_name] == "Success":
                    moment_url = s3_pre_uri + hashes[image_name]
                    thumbnail_url = get_thumbnail_url(moment_url)
                    caption = get_caption(image_name)
                    metadata = Moment.objects.create(
                        user_id=user,
                        caption=caption,
                        date_created=datetime.now(),
                        moment_url=moment_url,
                        thumbnail_url=thumbnail_url,
                        resource_path=hashes[image_name],
                        moment_category=moment,
                    )
                    metadata.save()
                    # Notify mentioned users
                    notify_mentioned_users(
                        notification_type="MOM_FRIEND",
                        mentioned_verbage=caption,
                        notification_verbage="Mentioned you in a moment!",
                        actor=user,
                        notification_object=metadata,
                    )

                    # Reward user with recent moment tagg
                    game_profile = GameProfile.objects.get(tagg_user=user.id)
                    rewards_list = json.loads(game_profile.newRewardsReceived)
                    if (
                        Moment.objects.filter(user_id=user).count() == 1
                        and "FIRST_MOMENT_POSTED" not in rewards_list
                    ):
                        rewards_list.append("FIRST_MOMENT_POSTED")
                        game_profile.newRewardsReceived = json.dumps(rewards_list)
                        game_profile.save()
                        increase_tagg_score(
                            user, TAGG_SCORE_ALLOTMENT["FIRST_MOMENT_POSTED"]
                        )

                    data.update(
                        {
                            "moment_id": metadata.moment_id,
                        }
                    )
            return validator.get_response(data=data, type=200)
        except ValidationError as err:
            self.logger.exception("There was a problem fetching the user details")
            return validator.get_response(
                data="There was a problem fetching the user details", type=500
            )
        except TaggScoreUpdateException as err:
            self.logger.exception("Tagg score update exception ")
            return validator.get_response(data="Tagg score update exception", type=500)
        except Exception as err:
            self.logger.exception("There was a problem trying to upload the images")
            return validator.get_response(
                data="There was a problem trying to upload the images", type=500
            )

    def list(self, request):
        """Retrieve moments from S3 (If a moment category is not passed, then all images uploaded by the user are returned)
        Args:
            pk = (int) user_id of the user
            moment = (str) moment category [NOT REQUIRED]
        Returns:
            (list) [moment_id, caption, date_created, path_hash, moment_category]
        """
        try:
            data = request.query_params
            if not check_is_valid_parameter("user_id", data):
                return validator.get_response(data="user_id is required", type=400)

            user_id, moment_category = data.get("user_id"), data.get("moment")
            user = TaggUser.objects.filter(id=user_id).first()
            if not user:
                return validator.get_response(data="User does not exist", type=404)

            if not allow_to_view_private_content(request.user, user):
                return Response([], status=status.HTTP_200_OK)
            serialized = MomentPostSerializer(
                get_user_moments(user, moment_category),
                many=True,
                context={"user": request.user},
            )
            return Response(serialized.data)
        except ValidationError as err:
            self.logger.exception("There was a problem fetching the user details")
            return validator.get_response(
                data="There was a problem fetching the user details", type=500
            )
        except Exception as err:
            self.logger.exception("There was a problem fetching the image details")
            return validator.get_response(
                data="There was a problem fetching the image details", type=500
            )

    @action(detail=False, methods=["post"])
    def create_video(self, request):
        """Create a moment object for video object after frontend finishes uploading to s3
        Args:
            caption: moment caption
            category: page moment was posted to
            filename: to determine the url to which the moment was posted to on s3
        """
        try:
            user = request.user
            body = json.loads(request.body)

            if not "caption" in body:
                self.logger.error("caption is required")
                return get_response(data="caption is required", type=400)

            if not check_is_valid_parameter("category", body):
                self.logger.error("category is required")
                return get_response(data="category is required", type=400)

            if not check_is_valid_parameter("filename", body):
                self.logger.error("filename is required")
                return get_response(data="filename is required", type=400)

            category = body["category"]
            caption = body["caption"]
            filename = body["filename"]

            # Check if user has enough coins to create moment
            if not has_enough_tagg_score(user, TAGG_SCORE_ALLOTMENT["MOMENT_POST"]):
                return Response("Not sufficient tagg score to post moment", status=400)

            # Create moment object, since upload in frontend was successful
            moment = Moment.objects.create(
                user_id=user,
                caption=caption,
                date_created=datetime.now(),
                moment_url=f"{settings.S3_VIDEO_BUCKET_URL}{settings.S3_MOMENTS_FOLDER}/{os.path.splitext(filename)[0]}.mp4",
                thumbnail_url=f"{settings.S3_VIDEO_BUCKET_URL}{settings.S3_THUMBNAILS_FOLDER}/{os.path.splitext(filename)[0]}-thumbnail.0000000.jpg",
                resource_path="don't think we're using",
                moment_category=category,
            )

            # Reward user with recent moment tagg
            game_profile = GameProfile.objects.get(tagg_user=user.id)
            rewards_list = json.loads(game_profile.newRewardsReceived)
            if (
                Moment.objects.filter(user_id=user).count() == 1
                and "FIRST_MOMENT_POSTED" not in rewards_list
            ):
                rewards_list.append("FIRST_MOMENT_POSTED")
                game_profile.newRewardsReceived = json.dumps(rewards_list)
                game_profile.save()
                increase_tagg_score(user, TAGG_SCORE_ALLOTMENT["FIRST_MOMENT_POSTED"])

            # the response we return the momentId the client will use to post tags
            return Response(
                {
                    "response_msg": "Success: Created video moment object",
                    "moment_id": moment.moment_id,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as err:
            self.logger.exception(
                "Internal server error occured while creating moment object"
            )
            return validator.get_response(
                data="Internal server error occured while creating moment object",
                type=500,
            )

    def retrieve(self, request, pk=None):
        try:
            moment = Moment.objects.get(moment_id=pk)
            if request.user.is_authenticated:
                serialized = MomentPostSerializer(
                    moment, context={"user": request.user}
                )
            else:
                serialized = PublicMomentPostSerializer(moment)
            return Response(serialized.data)
        except Moment.DoesNotExist:
            return Response("Moment not found", 400)
        except Exception as err:
            self.logger.exception(err)
            return Response("Something went wrong", 500)

    def patch(self, request, pk=None):
        """Update captions and tagging of Moment
        We use PATCH here due to convention, we're not replacing anything
        (that would be PUT), just updating data

        Args:
            moment_id = (str) Moment id
            caption = (dict) Caption for the moment
            (Optional)
            category: a new category for the moment
            tags (form data key): Array of tag objects [{Tag object}, {}, ...]
                + Tag objects {"x": "", "y": "", "z": "","user_id": ""}
                    - x: x coordinate
                    - y: y coordinate
                    - z: z coordinate
                    - user_id: user id of the user that must be tagged

        Returns:
            dict {image_name : upload_status} :
        """

        try:
            data = request.data

            if "moment_id" not in data:
                return Response("moment is required", 400)

            if "caption" not in data:
                return Response("caption is required", 400)

            moment_id = data.get("moment_id")
            caption = data.get("caption")

            moment = Moment.objects.get(moment_id=moment_id, user_id=request.user)

            moment.caption = caption

            if check_is_valid_parameter("category", data):
                category = data.get("category")
                moment.moment_category = category

            moment.save()

            if check_is_valid_parameter("tags", data):
                tags_output = replace_tags(self, request)
                if tags_output.status_code != 200:
                    return tags_output

            return Response("success")

        except Moment.DoesNotExist as err:
            self.logger.error(err)
            return Response("Moment id not found", 400)
        except Exception as err:
            self.logger.exception(err)
            return Response("There was a problem trying to update the moment", 500)

    def destroy(self, request, pk=None):
        try:
            moment = Moment.objects.get(moment_id=pk)
            if len(moment.moment_url.split(".com/")) >= 2:
                image_manager.remove_from_s3(moment.moment_url.split(".com")[1])

            moment.delete()
            return get_response(data="Success", type=200)

        except Moment.DoesNotExist:
            self.logger.error("Moment resource does not exist")
            return get_response(data="Moment resource does not exist", type=400)
        except ValueError:
            self.logger.exception("Malformed resource id")
            return get_response(data="Malformed resource id", type=400)
        except ValidationError:
            self.logger.exception("Moment resource not found")
            return get_response(data="Moment resource not found", type=400)
        except Exception:
            self.logger.exception("There was a problem with deleting the moment")
            return get_response(
                data="There was a problem with deleting the moment", type=500
            )

    @action(detail=False, methods=["get"])
    def tags(self, request):
        try:
            data = request.query_params
            if not check_is_valid_parameter("moment_id", data):
                return Response("moment_id is required", 400)
            taglists = MomentTagList.objects.filter(moment_id=data["moment_id"])
            serialized = MomentTagSerializer(
                [o.moment_tag for o in taglists], many=True
            )
            return Response(serialized.data)
        except Exception:
            self.logger.exception("Something went wrong")
            return Response("Something went wrong", 500)

    @action(detail=False, methods=["get"])
    def all_moment(self, request):
        data = request.query_params
        if not check_is_valid_parameter("user_id", data):
            return Response("user_id is required", 400)
        user = TaggUser.objects.filter(id=data["user_id"])
        if not user:
            return Response("Invalid user id", 400)
        user = user[0]
        categories = list(set(json.loads(user.momentcategory.moments_category)))
        dt = {"moment_category": categories, "moment-list": []}
        for category in categories:
            dt["moment-list"].append(
                {
                    category: MomentPostSerializer(
                        get_user_moments(user, category),
                        many=True,
                        context={"user": user},
                    ).data
                }
            )
        return Response(dt)

    @action(detail=False, methods=["post"])
    def update_tags(self, request):
        data = request.data
        if not check_is_valid_parameter("moment_id", data):
            return Response("moment_id is required", 400)

        if not check_is_valid_parameter("moments_category", data):
            return Response("moment_category_id is required", 400)
        mtag = MomentCategory.objects.filter(user_id=request.user)
        if not mtag:
            return Response("No category created by you.", 400)
        mtag = mtag[0]
        if not data["moments_category"] in json.loads(mtag.moments_category):
            return Response("Invalid moments category", 400)
        moment = Moment.objects.filter(
            moment_id=data["moment_id"], user_id=request.user
        )
        if not moment:
            return Response("Invalid moment.", 400)
        moment = moment[0]

        # if moment.moment_category == data["moments_category"]:
        #     return Response("Moment already exist against same tage.", 400)

        moment.moment_category = data["moments_category"]
        moment.save()
        return Response("Successfully update moments with tags", 200)

    @action(detail=False, methods=["get"])
    def check_done_processing(self, request):
        try:
            data = request.query_params
            if not check_is_valid_parameter("moment_id", data):
                return Response("moment_id is required", 400)
            moment = Moment.objects.get(moment_id=data["moment_id"])

            if (
                requests.get(moment.thumbnail_url).status_code == 200
                and requests.get(moment.moment_url).status_code == 200
            ):
                return Response("Done Processing")
            else:
                return Response("Still processing", 400)

        except Moment.DoesNotExist:
            return Response("Invalid moment_id", 400)
        except Exception as e:
            self.logger.exception(e)
            return Response("Something went wrong", 500)


class MomentThumbnailViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(MomentThumbnailViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def retrieve(self, request, pk=None):
        """Handles a GET request to this endpoint (with pk)."""
        try:
            moment_object = Moment.objects.filter(moment_id=pk).first()

            # Prevent unauthorized user from viewing a user's thumbnail view of their moment
            user = TaggUser.objects.filter(id=moment_object.user_id_id).first()
            if not allow_to_view_private_content(request.user, user):
                return Response("Account is private", status=status.HTTP_403_FORBIDDEN)

            if not moment_object:
                return validator.get_response(data="Moment does not exist", type=404)

            moment, ext = os.path.splitext(moment_object.resource_path)

            moment = "thumbnails/" + moment + "-thumbnail.jpg"

            client = boto3.client("s3")

            image_obj = client.get_object(
                Bucket=settings.S3_BUCKET,
                Key=moment,
            )["Body"].read()
            return HttpResponse(image_obj, status=status.HTTP_200_OK)

        except ValidationError as err:
            self.logger.exception(
                "There was a problem fetching the moment details, maybe it does not exist"
            )
            return validator.get_response(
                data="There was a problem fetching the moment details, maybe it does not exist",
                type=500,
            )
        except Exception as error:
            self.logger.exception(error)
            return Response(
                "Something went wrong", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MomentDiscoverViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    pagination_class = DiscoverMomentsPaginator

    def __init__(self, *args, **kwargs):
        super(MomentDiscoverViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        try:
            user = request.user

            # SF - commenting out since we're using naive approach to unblock prod, speed up performance and improve recos
            # suggested_moments = get_moment_recommendataions(user)

            # if not suggested_moments:
            #     suggested_moments = suggest_moments_naive(user)

            suggested_moments = suggest_moments_naive(user)

            return Response(
                MomentPostSerializer(
                    suggested_moments, many=True, context={"user": user}
                ).data
            )
        except Exception as e:
            self.logger.exception(e)
            return Response("Something went wrong", 500)

    @action(detail=False, methods=["get"], permission_classes=[AllowAny])
    def get_dm_view_stage(self, request):
        try:
            data = request.query_params

            if not check_is_valid_parameter("user_id", data):
                return Response("user_id required to be provided in query params", 400)

            if not TaggUser.objects.filter(id=data.get("user_id")).exists():
                return Response("User does not exist", 404)

            user = TaggUser.objects.get(id=data.get("user_id"))
            dm_view_stage = user.taggusermeta.dm_view_stage
            timestamp_dm_view_stage = user.taggusermeta.timestamp_dm_view_stage

            return Response(
                {
                    "dm_view_stage": dm_view_stage,
                    "timestamp_dm_view_stage": timestamp_dm_view_stage,
                },
                200,
            )

        except TypeError as err:
            logging.exception(
                "There was a type error while retrieving dm view stage ", err
            )
            return Response(
                "There was a type error while retrieving dm view stage", 403
            )

        except Exception as err:
            logging.exception(
                "There was a problem while retrieving the dm view stage ", err
            )
            return Response(
                "There was a problem while retrieving the dm view stage", 500
            )

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def update_dm_view_stage(self, request):
        """Legal states:

        Stage 0 -> Stage 1
        today       today
        today       tomorrow

        Stage 1 -> Stage 2
        today       today
        today       tomorrow not allowed!

        Stage 2 -> Stage 0
        today       today
        today       tomorrow

        """
        try:
            data = request.data

            if not "user_id" in data:
                return Response("user_id required to be provided via raw JSON", 400)

            if not "dm_view_stage" in data:
                return Response(
                    "dm_view_stage required to be provided via raw JSON", 400
                )

            if not TaggUser.objects.filter(id=data.get("user_id")).exists():
                return Response("User does not exist", 404)

            user = TaggUser.objects.get(id=data.get("user_id"))

            # Ensure that the stage progression is correct here
            current_stage = user.taggusermeta.dm_view_stage
            received_stage = data["dm_view_stage"]

            current_stage_time = user.taggusermeta.timestamp_dm_view_stage
            now = pytz.UTC.localize(datetime.now())

            if (
                (
                    current_stage == 0
                    and received_stage == 1
                    and current_stage_time.date() <= now.date()
                )
                or (
                    current_stage == 1
                    and received_stage == 2
                    and current_stage_time.date() == now.date()
                )
                or (
                    current_stage == 2
                    and received_stage == 0
                    and current_stage_time.date() < now.date()
                )
            ):
                user.taggusermeta.dm_view_stage = received_stage
                user.taggusermeta.timestamp_dm_view_stage = now
                user.save()

            return Response("Success", 200)

        except TypeError as err:
            logging.exception(
                "There was a type error while updating dm view stage ", err
            )
            return Response("There was a type error while updating dm view stage", 403)

        except Exception as err:
            logging.exception(
                "There was a problem while updating the dm view stage ", err
            )
            return Response("There was a problem while updating the dm view stage", 500)


class MomentCreateViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(MomentCreateViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        user = request.user
        if user:
            # Check if user has enough coins to create moment
            if not has_enough_tagg_score(user, TAGG_SCORE_ALLOTMENT["MOMENT_POST"]):
                return Response("Not sufficient tagg score to post moment", status=400)

            momentsObject = Moment.objects.filter(
                moment_id=request.data.get("moment_id")
            ).first()
            if momentsObject:
                momentsVisitedObject = MomentViews.objects.create(
                    moment_viewer=user,
                    moment_viewed=momentsObject,
                )
                momentsVisitedObject.save()

                return Response("data got created", status=200)
            else:
                return Response("data not found", status=400)



class MomentListViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]

    def __init__(self, *args, **kwargs):
        super(MomentListViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
    
    def list(self, request):
        data = request.query_params
        lastMoment = {
            "moment_id": "reached-limit-on-discover-moments",
        }

        if not check_is_valid_parameter("user_id", data):
            return Response("user_id required to be provided in query params", 400)

        if not TaggUser.objects.filter(id=data.get("user_id")).exists():
            return Response("User does not exist", 404)
        user = TaggUser.objects.filter(id=data.get("user_id")).first()    
        listMoment = []

        meta = TaggUserMeta.objects.filter(user=user)[0]
        dm_view_stage = meta.dm_view_stage

        nextRefreshTime = pytz.UTC.localize(datetime.now())
        if nextRefreshTime.hour < 5:
            nextRefreshTime.replace(hour=5)
        else:
            nextRefreshTime += timedelta(days=1)
            nextRefreshTime.replace(hour=5)
            
        # if dm_view_stage == 2 and meta.timestamp_dm_view_stage < nextRefreshTime:
        #     listMoment.append(lastMoment)
        #     return Response(listMoment, 200)

        today = datetime.now().date()
        Obj = DailyMoment.objects.filter(user=user, status=False).order_by('-date')[:7]
        for items in Obj:
            momentsObject = Moment.objects.filter(moment_id=items.moment_id).first()
            if momentsObject:
                data = MomentPostSerializer(
                    momentsObject,
                    many=False,
                    context={"user": user},
                ).data
                listMoment.append(data)
            
        listMoment.sort(key=itemgetter('date_created'), reverse=True)    
        listMoment.append(lastMoment)
        return Response(listMoment, status=200)
        
    # def list(self, request):
    #     data = request.query_params
    #     lastMoment = {
    #         "moment_id": "reached-limit-on-discover-moments",
    #     }

    #     if not check_is_valid_parameter("user_id", data):
    #         return Response("user_id required to be provided in query params", 400)

    #     if not TaggUser.objects.filter(id=data.get("user_id")).exists():
    #         return Response("User does not exist", 404)

    #     user = TaggUser.objects.get(id=data.get("user_id"))

    #     listMoment = []

    #     # If user is in stage 2, do not send any moments
    #     meta = TaggUserMeta.objects.filter(user=user)[0]
    #     dm_view_stage = meta.dm_view_stage

    #     nextRefreshTime = pytz.UTC.localize(datetime.now())
    #     if nextRefreshTime.hour < 5:
    #         nextRefreshTime.replace(hour=5)
    #     else:
    #         nextRefreshTime += timedelta(days=1)
    #         nextRefreshTime.replace(hour=5)
    #     if dm_view_stage == 2 and meta.timestamp_dm_view_stage < nextRefreshTime:
    #         listMoment.append(lastMoment)
    #         return Response(listMoment, 200)

    #     momentsObject = Moment.objects.all()
    #     momentUsersList = []
    #     if momentsObject:
    #         for items in momentsObject:
    #             momentsVisitedObject = MomentViews.objects.filter(
    #                 moment_viewer=user,
    #                 moment_viewed=items,
    #             ).first()

    #             if len(listMoment) == 7:
    #                 break
    #             # check if user is already in the list
    #             if str(items.user_id_id) not in momentUsersList:
    #                 if not momentsVisitedObject and items.user_id_id != user.id:
    #                     data = MomentPostSerializer(
    #                         items,
    #                         many=False,
    #                         context={"user": user},
    #                     ).data
    #                     # self.logger.info("test id: {}".format(str(data["user"]["id"])))
    #                     listMoment.append(data)
    #                     momentUsersList.append(data["user"]["id"])

    #         listMoment.append(lastMoment)
    #         return Response(listMoment, status=200)

    #     else:
    #         return Response(listMoment, status=204)


class ProfileRewardViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(ProfileRewardViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def put(self, request, pk=None):
        try:
            user = request.user
            userObj = TaggUser.objects.filter(id=user.id).first()
            if userObj:
                if request.data.get("type"):
                    userObj.reward = request.data.get("type")
                if request.data.get("thumbnail_enable"):
                    userObj.thumbnail_enable = request.data.get("thumbnail_enable")
                userObj.save()
                return Response("Successfully Updated", 200)
        except Exception as error:
            logging.error(error)
            return Response("Something went wrong", 500)

    def list(self, request):
        user = request.user
        userObj = TaggUser.objects.filter(id=user.id).first()
        end = datetime.now()
        start = end - timedelta(hours=24)
        is_edit_tags = Widget.objects.filter(
            owner_id=user.id,
            updated_on__gte=start,
            updated_on__lte=end,
            edit_count__gte=1,
        )[:2]
        if len(is_edit_tags) == 2:
            Widget.objects.filter(owner_id=user.id).update(status="unlock")
        if userObj:

            return Response({"status": userObj.reward}, status=200)
            return Response(
                {
                    "status": userObj.reward,
                    "thumbnail_enable": userObj.thumbnail_enable,
                    "edit_count": is_edit_tags,
                },
                status=200,
            )
        else:
            return Response("no data", status=400)


class DailyMomentViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(DailyMomentViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        user = request.user
        moment = request.data.get("moment")
        if user:
            Obj = DailyMoment.objects.filter(user=user, moment=moment).first()
            if Obj:
                Obj.status = True
                Obj.save()
                return Response("data got created", status=200)
            else:
                return Response("data not found", status=400)

    def list(self, request):
        data = request.query_params
        lastMoment = {
            "moment_id": "reached-limit-on-discover-moments",
        }

        if not check_is_valid_parameter("user_id", data):
            return Response("user_id required to be provided in query params", 400)

        if not TaggUser.objects.filter(id=data.get("user_id")).exists():
            return Response("User does not exist", 404)
        user = TaggUser.objects.filter(id=data.get("user_id")).first()    
        today = datetime.now().date()
        Obj = DailyMoment.objects.filter(user=user, status=False).order_by('-date')[:7]
        listMoment = []
        momentUsersList = []
        for items in Obj:
            momentsObject = Moment.objects.filter(moment_id=items.moment_id).first()
            data = MomentPostSerializer(
                momentsObject,
                many=False,
                context={"user": user},
            ).data
            listMoment.append(data)
            momentUsersList.append(data["user"]["id"])
        listMoment.append(lastMoment)
        return Response(listMoment, status=200)


class PermissionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(PermissionViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request):
        user = request.user
        data=request.data
        if user:
            Obj = TaggUserMeta.objects.filter(user=user).first()
            if Obj:
                if "contact" in data:
                    Obj.contact_permission=True
                if "location" in data:
                    Obj.location_permission=True
                if "notification" in data:
                    Obj.notification_permission=True
                if "notification" and "location" and "contact" in data:
                    Obj.permission_completed=True
                    Obj.save()
                return Response({"message":"permission got created","status":200,"permission_status":True}, status=200)
            else:
                return Response({"message":"permission got created","status":400,"permission_status":False}, status=400)

    def list(self, request):
        user = request.user
        taggData=TaggUserMeta.objects.filter(user=user).first()    
        data={
            "status":taggData.permission_completed,
            "contact":taggData.contact_permission,
            "location":taggData.location_permission,
            "notification":taggData.notification_permission,
        }
        return Response(data, status=200)

class InviteUsersViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(InviteUsersViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self,request):
        user = request.user
        data = request.POST
        if not check_is_valid_parameter("invitee_phone_number", data):
            return Response("invitee_phone_number is required", 400)

        if not check_is_valid_parameter("invitee_first_name", data):
            return Response("invitee_first_name is required", 400)

        if not check_is_valid_parameter("invitee_last_name", data):
            return Response("invitee_last_name is required", 400)    
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        inviteObj=InvitedUser.objects.filter(phone_number=data.get("invitee_phone_number"))
        message_body = "Hey! Use my referral link to join Tagg and we both get 10 coins "+"https://apps.apple.com/us/app/tagg-creator-tool-community/id1537853613" 
        message = client.messages.create(
            to=data.get("invitee_phone_number"), from_=settings.TWILIO_PHONE_NUMBER, body=message_body
        )
        if message:
            if not inviteObj:
                InvitedUser.objects.create(inviter=user,phone_number=data.get("invitee_phone_number"),first_name=data.get("invitee_first_name"),last_name=data.get("invitee_last_name"),status="INVITED")
                return Response({"Status":"message sent succefully"}, status=200)
            else:
                return Response({"Status":"message sent succefully"}, status=200)

class InvitedViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(InvitedViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        user = request.user
        data=InvitedUser.objects.filter(inviter=user).extra(
            select={
                'phoneNumber': 'phone_number',
                'firstName':'first_name',
                'lastName':'last_name',
                'status':'status'
            }
        ).values('phoneNumber','firstName','lastName','status')
        if data:
            for item in data:
                users=TaggUser.objects.filter(phone_number=item['phoneNumber']).first()
                if item['status']=='JOINED':
                    item["thumbnailUrl"] = profile_pic_url(users.id)
                else:
                    item["thumbnailUrl"]="no-thumbnail-url"
                            
            info={
                'inviteeList':data,
                'joinedCount':sum((1 for items in data if items.get('status')=='JOINED')),
                'coinsEarned':sum((1 for items in data if items.get('status')=='JOINED'))*10,
            }
        else:
            info={
                'inviteeList':[],
                'joinedCount':0,
                'coinsEarned':0,
            }    
        return Response(info, status=200)

class SkinPermissionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = None

    def __init__(self, *args, **kwargs):
        super(SkinPermissionViewSet, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        user = request.user
        Obj = TaggUserMeta.objects.filter(user=user).first()
        if Obj:
            info={
                'background_permission':Obj.background_gradient_permission,
                'tab_permission':Obj.tab_permission,
            }       
            return Response(info, status=200)

    def create(self,request):
        user = request.user
        data = request.POST
        Obj = TaggUserMeta.objects.filter(user=user).first()
        game_profile = GameProfile.objects.filter(tagg_user=user).first()
        if Obj and game_profile:
            if data.get('background_permission') and Obj.background_gradient_permission==False:
                Obj.background_gradient_permission=data.get('background_permission')
                game_profile.tagg_score = game_profile.tagg_score-25
            if data.get('tab_permission') and Obj.tab_permission==False:
                Obj.tab_permission=data.get('tab_permission')
                game_profile.tagg_score = game_profile.tagg_score-25
            if game_profile.tagg_score>=0:
                Obj.save()
                game_profile.save()
                return Response({"message":"data updated Succesfully"}, status=200)
            else:
                return Response({"message":"game point are less"}, status=200)