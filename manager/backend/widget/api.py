import json
import logging, datetime

from django.conf import settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ViewSet

from ..gamification.models import GameProfile

from ..common.constants import HOMEPAGE
from ..common.image_manager import remove_from_s3, profile_pic_url
from ..common.validator import check_is_valid_parameter, get_response
from ..gamification.constants import TAGG_SCORE_ALLOTMENT
from ..gamification.utils import increase_tagg_score, determine_gamification_tier, TaggTierException
from ..models import TaggUser
from ..moments.moment_category.utils import get_moment_categories
from ..moments.models import Moment
from ..gamification.models import GameProfile
from ..common import validator
from .models import (
    ApplicationLinkWidget,
    GenericLinkWidget,
    SocialMediaWidget,
    VideoLinkWidget,
    Widget,
    WidgetType,
    RewardCalculation,
    rgetattr,
    TaggTitleFontColorUnlock,
    TaggBackgroundImageUnlock,
    TaggThumbnailImageUnlock,
)
from .serializers import (
    ApplicationLinkWidgetSerializer,
    GenericLinkWidgetSerializer,
    SocialMediaWidgetSerializer,
    VideoLinkWidgetSerializer,
    WidgetSerializer,
)
from ..gamification.serializers import GameProfileSerializer
from .utils import create_presigned_post, generateFilePath, uploadThumbnail
from ..common.notification_manager import (
    NotificationType,
    handle_bulk_notification,
    handle_notification,
    handle_notification_with_images,
)


class PresignedURLViewset(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super(PresignedURLViewset, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        """Generate Presigned URL to send to client
            URL : /api/presigned-url/create/

         Args:
            filename - this is something we should generate ourselves either in the frotnend or the backend
            should be a unique identifier like a hash or someth
            We will want to have a more sophisticated organizational system for how we manage uploads
            We should handle bucket/object naming schemes and every other 'create_presigned_post' param

        Returns:
            A URL
            A status code
        """
        # verifying the payload is valid - username or email. - we can just get this from async storage
        try:
            body = json.loads(request.body)
            if not check_is_valid_parameter("filename", body):
                self.logger.error("filename is required")
                return get_response(data="filename is required", type=400)

            filename = settings.S3_THUMBNAILS_FOLDER + "/" + body["filename"]

            # want to generate presigned URL here and return it, if possible.
            upload_url = create_presigned_post(filename)
            if upload_url:
                # the response we return will give us the URL the client will use to make the POST request to, and a set of x-amz fields to use as credentials
                return Response(
                    {
                        "response_msg": "Success: Generated a url",
                        "response_url": upload_url,
                        "image_path": "https://"
                        + settings.S3_BUCKET
                        + "."
                        + settings.S3_PRE_OBJECT_URI
                        + "/"
                        + str(filename),
                    }
                )
            else:
                return get_response(data="Problem generating presigned url", type=500)
        except TaggUser.DoesNotExist:
            self.logger.error("Invalid user Id.")
            return get_response(data="Invalid user ID.", type=404)
        except Exception as err:
            self.logger.exception("Problem generating presigned url")
            self.logger.exception(err)
            return get_response(data="Problem generating presigned url", type=500)


class WidgetViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = WidgetSerializer
    pagination_class = LimitOffsetPagination
    queryset = Widget.objects.select_subclasses()
    http_method_names = ["get", "post", "delete"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        widgets = Widget.objects.filter(
            owner=request.user, active=True
        ).select_subclasses()
        paginated_widgets = self.paginate_queryset(widgets)
        return self.get_paginated_response(
            WidgetSerializer(paginated_widgets, many=True).data
        )

    def destroy(self, request, *args, **kwargs):
        try:
            widget = self.get_object()
            if not isinstance(widget, SocialMediaWidget):
                userId = request.user.id
                url = widget.url
                remove_from_s3(generateFilePath(url, userId))
            if getattr(widget, "moment_id", None):
                widget.moment_id = None
            widget.active = False
            widget.save()
            return Response("Success", 204)
        except Exception as err:
            self.logger.exception(err)
            return Response("Internal Server Error", 500)

    @swagger_auto_schema(
        method="get",
        manual_parameters=[
            openapi.Parameter("user_id", openapi.IN_QUERY, type=openapi.TYPE_STRING)
        ],
    )
    @action(detail=False, methods=["get"])
    def store(self, request):
        if "user_id" not in request.GET:
            self.logger.error("user_id is a required field")
            raise ValidationError({"user_id": "This field is required."})
        user = TaggUser.objects.get(id=request.GET.get("user_id"))
        categories = get_moment_categories(user)

        result = {}

        for category in categories:
            result[category] = WidgetSerializer(
                Widget.objects.filter(
                    owner=user,
                    active=True,
                    page=category,
                )
                .order_by("order")
                .select_subclasses(),
                many=True,
            ).data[:20]
        # self.logger.info("test TOTAL: {}".format(result))
        return Response(result)

    @action(detail=False, methods=["post"])
    def store_widget(self, request):
        if "user_id" not in request.GET:
            self.logger.error("user_id is a required field")
            raise ValidationError({"user_id": "This field is required."})
        user = TaggUser.objects.get(id=request.GET.get("user_id"))
        try:
            for _widget in request.data.get("widget", []):
                widget = Widget.objects.get(id=_widget.get("id"), owner=user)
                widget.order = _widget.get("order")
                widget.save()
        except:
            pass
        categories = get_moment_categories(user)
        result = {}
        for category in categories:
            result[category] = WidgetSerializer(
                Widget.objects.filter(
                    owner=user,
                    page=category,
                )
                .order_by("order")
                .select_subclasses(),
                many=True,
            ).data[:20]
        return Response(result)

    @action(detail=True, methods=["post"], url_path="image")
    def upload_image(self, request):
        widget = self.get_object()
        if request.FILES.get("image"):
            widget.custom_image = request.FILES.get("image")
            widget.edit_count += 1
            widget.save()
        return Response(WidgetSerializer(widget).data, status=200)


class WidgetTypeBaseViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

    def create(self, request, *args, **kwargs):
        request.data["type"] = self.widget_type
        request.data["owner"] = request.user.id

        self.get_serializer(data=request.data).is_valid(raise_exception=True)

        if request.data["page"] != HOMEPAGE:
            raise ValidationError({"page": "Taggs can be added only to Home page"})

        #tma2087 flag used to increase tagg score for uploading image
        thumbnail_upload_flag = False
        if "thumbnail_url" in request.data:
            thumbnail_url = uploadThumbnail(
                request.data["thumbnail_url"],
                request.user.id,
                request.data["link_type"],
            )
            if thumbnail_url != "":
                request.data["thumbnail_url"] = thumbnail_url
                #tma2087
                thumbnail_upload_flag = True

        order = int(request.data["order"])
        widgets = Widget.objects.filter(
            owner=request.user,
            page=request.data["page"],
            active=True,
        )

        if order < 0 or order > len(widgets):
            self.logger.error("Invalid order value")
            return Response("Invalid order value", 400)

        for w in widgets:
            if w.order >= order:
                w.order += 1
                w.save()

        # Increase tagg score for adding a widget
        increase_tagg_score(request.user, TAGG_SCORE_ALLOTMENT["TAGG_CREATE"])

        # tma2087 Increase tagg score for uploading a thumbnail
        if thumbnail_upload_flag == True:
            increase_tagg_score(request.user, TAGG_SCORE_ALLOTMENT["TAGG_EDIT"])

        # send notification to all other users when adding tagg
        if TaggUser.objects.filter(id=request.user.id, taggusermeta__is_onboarded=True).exists():
            if handle_bulk_notification(
                NotificationType.DEFAULT,
                request.user,
                f"{request.user.username} created a new tagg. Tap in to see what its all about!! 👀",
            ):
                self.logger.info(f"Sent notification for {request.user.username}")
            else:
                self.logger.info(
                    f"Failed sending notification for {request.user.username}"
                )

        response = super().create(request, *args, **kwargs)

        return response

    def partial_update(self, request, *args, **kwargs):
        if "owner" in request.data or "type" in request.data:
            self.logger.error("Not allowed to update: owner | type")
            return Response("Not allowed to update: owner | type", 400)

        if "page" in request.data and request.data["page"] not in get_moment_categories(
            request.user
        ):
            raise ValidationError({"page": "User does not have that page name."})

        instance = self.get_object()

        color_keys = [
            "border_color_start",
            "border_color_end",
            "background_color_start",
            "background_color_end",
            "font_color",
        ]

        widget = Widget.objects.get(id=instance.id, active=True)

        #tma2087 and tma2101 flag used to increase tagg score
        tagg_edit_flag = False

        if (
            "thumbnail_url" in request.data
            and instance.thumbnail_url != request.data["thumbnail_url"]
        ):
            # delete old thumbnailurl from s3
            
            userId = request.user.id
            url = instance.thumbnail_url
            remove_from_s3(generateFilePath(url, userId))

            thumbnail_url = uploadThumbnail(
                request.data["thumbnail_url"],
                request.user.id,
                request.data["link_type"],
            )
            if thumbnail_url != "":
                request.data["thumbnail_url"] = thumbnail_url
                #tma2087 and tma2101
                tagg_edit_flag = True
            else:
                request.data[
                    "thumbnail_url"
                ] = "https://tagg-prod.s3.us-east-2.amazonaws.com/misc/not+found.jpg"

        for key in color_keys:
            if key in request.data:
                sub_object = ""
                if isinstance(instance, VideoLinkWidget):
                    sub_object = "videolinkwidget"
                if isinstance(instance, ApplicationLinkWidget):
                    sub_object = "applicationlinkwidget"
                if isinstance(instance, GenericLinkWidget):
                    sub_object = "genericlinkwidget"
                elif isinstance(instance, SocialMediaWidget):
                    sub_object = "socialmediawidget"

                path = sub_object + "." + key
                if sub_object and rgetattr(widget, path) != request.data[key]:
                    #tma2101
                    tagg_edit_flag = True
                    break

        if "order" in request.data:
            instance = self.get_object()
            old_order = instance.order
            new_order = int(request.data["order"])
            widgets = Widget.objects.filter(
                owner=instance.owner, page=instance.page, active=True
            )
            if new_order < 0 or new_order >= len(widgets):
                raise ValidationError({"order": "Invalid value."})
            # first, remove this instance from all orders
            for w in widgets:
                if w.order >= old_order + 1:
                    w.order -= 1
                    w.save()
            # then, make space for this new widget location
            for w in widgets:
                if w.order >= new_order:
                    w.order += 1
                    w.save()

        # tma2101
        if "background_url" in request.data and instance.background_url != request.data.get("background_url"):
            tagg_edit_flag = True

        if instance.status == "lock":
            st = False
            if hasattr(
                instance, "font_color"
            ) and instance.font_color != request.data.get("font_color"):
                st = True
            if hasattr(instance, "url") and instance.url != request.data.get("url"):
                st = True
            if hasattr(instance, "title") and instance.title != request.data.get(
                "title"
            ):
                st = True
            if (
                hasattr(instance, "background_color_start")
                and instance.background_color_start
                != request.data.get("background_color_start")
                and request.data.get("background_color_start")
            ):
                st = True
            if (
                hasattr(instance, "background_color_end")
                and instance.background_color_end
                != request.data.get("background_color_end")
                and request.data.get("background_color_end")
            ):
                st = True
            if (
                hasattr(instance, "username")
                and instance.username != request.data.get("username")
                and request.data.get("username")
            ):
                st = True
            # if st:
            #     instance.edit_count += 1
            total_sec = round(
                datetime.datetime.now().timestamp() - instance.updated_on.timestamp(), 2
            )
            if st and total_sec < (24 * (60 * 60)):
                instance.edit_count = 1
        instance.save()

        # tma2087 and tma2101 Increase tagg score for editing tagg
        if tagg_edit_flag == True:
            increase_tagg_score(request.user, TAGG_SCORE_ALLOTMENT["TAGG_EDIT"])

        return super().partial_update(request, *args, **kwargs)


class VideoLinkWidgetViewSet(WidgetTypeBaseViewSet):
    serializer_class = VideoLinkWidgetSerializer
    widget_type = WidgetType.VIDEO_LINK
    queryset = VideoLinkWidget.objects.all()


class ApplicationLinkWidgetViewSet(WidgetTypeBaseViewSet):
    serializer_class = ApplicationLinkWidgetSerializer
    widget_type = WidgetType.APPLICATION_LINK
    queryset = ApplicationLinkWidget.objects.all()


class GenericLinkWidgetViewSet(WidgetTypeBaseViewSet):
    serializer_class = GenericLinkWidgetSerializer
    widget_type = WidgetType.GENERIC_LINK
    queryset = GenericLinkWidget.objects.all()


class SocialMediaWidgetViewSet(WidgetTypeBaseViewSet):
    serializer_class = SocialMediaWidgetSerializer
    widget_type = WidgetType.SOCIAL_MEDIA
    queryset = SocialMediaWidget.objects.all()
class RewardCalculations(ModelViewSet):
    queryset = RewardCalculation.objects.all()

    def create(self, request):
        taggId = request.data.get("taggId")
        if not taggId:
            return Response("taggId is a required field", 400)

        taggId = taggId.strip()

        widgetObj = Widget.objects.filter(id=taggId).first()
        if not widgetObj:
            return Response(f"No widget found for id: {taggId}", 404)

        if widgetObj.owner.blocked.exists():
            # owner is blocked
            return Response(f"owner of Widget({widgetObj.id}) is blocked", 403)

        rewardObj = RewardCalculation.objects.filter(
            userId=widgetObj.owner, taggId=taggId
        ).first()
        if rewardObj:
            if rewardObj.count > 30:
                gameObj = GameProfile.objects.filter(tagg_user=widgetObj.owner).first()

                handle_notification_with_images(
                    NotificationType.CLICK_TAG,
                    widgetObj.owner,
                    widgetObj.owner,
                    "Tagg Click Count",
                    "Your Taggs are getting clicked!  Here’s some Tagg coin!",
                    profile_pic_url(widgetObj.owner.id),
                )
                if gameObj:
                    gameObj.tagg_score = gameObj.tagg_score + 5
                    rewardObj.count = 0
                    rewardObj.save()
                    gameObj.save()
                    # tma-2031
                    gameObj.tier = determine_gamification_tier(gameObj.tagg_score)
                    gameObj.save()
                    return Response("successfully saved data", 200)
            else:
                rewardObj.count = rewardObj.count + 1
                rewardObj.save()
                return Response("successfully saved data", 200)
        else:
            RewardCalculation.objects.create(userId=widgetObj.owner, taggId=widgetObj)
            return Response("successfully saved data", 200)
class RewardsAdd(ModelViewSet):
    permission_classes = [IsAuthenticated]

    def create(self, request):
        data=request.data
        if "coins" not in data:
            return Response("coins is required", 400)

        coins = data.get("coins")
        gameObj = GameProfile.objects.filter(tagg_user=request.user).first()
        if gameObj:
            gameObj.tagg_score = gameObj.tagg_score +int(coins)
            gameObj.save()
            # tma-2031
            gameObj.tier = determine_gamification_tier(gameObj.tagg_score)
            gameObj.save()
            return Response("successfully saved data", 200)



# tma-1980, Unlocks feature to change background of any tagg
class UnlockBackground(ViewSet):
    def __init__(self, **kwargs):
        super(UnlockBackground, self).__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    def list(self, request):
        try:
            userId = request.query_params.get("userId")
            flag = False
            gameObj = GameProfile.objects.filter(tagg_user=userId).first()
            unlockObj = TaggBackgroundImageUnlock.objects.filter(user=userId).exists()
            # To check if user is eligible to unlock feature or not
            if unlockObj == False:
                new_user = TaggBackgroundImageUnlock.objects.create(
                    user=gameObj.tagg_user,
                )
                new_user.save()
            unlockObj2 = TaggBackgroundImageUnlock.objects.filter(user=userId).first()
            if gameObj and unlockObj2.tagg_bg_image_unlocked == False:
                if gameObj.tagg_score >= 20:
                    flag = True
            # To check if the user has already unlocked the feature.
            elif unlockObj2.tagg_bg_image_unlocked == True:
                return Response("already unlocked tagg background feature", 200)
            to_return = {
                "unlock_background": flag,
            }
            return Response(to_return, 200)
        except Exception as err:
            self.logger.exception(
                "There was a problem to show unlock background pop-up"
            )
            return validator.get_response(
                data="There was a problem to show unlock background pop-up",
                type=500,
            )

    def create(self, request):
        try:
            # if the user clicks on button to unlock the tagg bg feature, their tagg score will get reduced by 20 and Game Profile table will store their feature unlock status as True
            userId = request.data.get("userId")
            gameObj = GameProfile.objects.filter(tagg_user=userId).first()
            unlockObj = TaggBackgroundImageUnlock.objects.filter(user=userId).first()
            if (
                gameObj
                and unlockObj.tagg_bg_image_unlocked == False
                and gameObj.tagg_score >= 20
            ):
                unlockObj.tagg_bg_image_unlocked = True
                unlockObj.save()
                gameObj.tagg_score = gameObj.tagg_score - 20
                gameObj.save()
                # tma-2031
                gameObj.tier = determine_gamification_tier(gameObj.tagg_score)
                gameObj.save()
                return Response("successfully updated tagg score", 200)
            elif gameObj.tagg_score < 20 and unlockObj.tagg_bg_image_unlocked == False:
                return Response(
                    "not enough score to unlock tagg background functionality", 200
                )
            else:
                return Response(
                    "User already unlocked the tagg background functionality", 200
                )
        except TaggTierException as err:
            self.logger.exception(
                "There was a problem in updating tier for user"
            )
            return validator.get_response(
                data="There was a problem in updating tier for user",
                type=500,
            )
        except Exception as err:
            self.logger.exception(
                "There was a problem in unlocking the tagg background functionality for the user"
            )
            return validator.get_response(
                data="There was a problem in unlocking the tagg background functionality for the user",
                type=500,
            )

    @action(detail=False, methods=["get"])
    def is_award_shown(self, request):
        user = request.user
        data = {"is_award_shown": False}
        unlockObj = TaggBackgroundImageUnlock.objects.filter(user=user).first()
        if not unlockObj:
            return Response(data, status=200)
        data["is_award_shown"] = unlockObj.is_award_shown
        return Response(data, status=200)

    @action(detail=False, methods=["post"])
    def award_shown(self, request):
        user = request.user
        data = {"is_award_shown": False}
        unlockObj = TaggBackgroundImageUnlock.objects.filter(user=user).first()
        if not unlockObj:
            return Response(
                "TaggBackgroundImageUnlock object for user doesn'\t exist", status=200
            )
        unlockObj.is_award_shown = True
        unlockObj.save()
        data["is_award_shown"] = unlockObj.is_award_shown
        return Response(data, status=200)


# tma-1982, Unlocks feature to change font color of title of any tagg
class UnlockTaggTitleFontColor(ViewSet):

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]

    @action(detail=False, methods=["get"])
    def is_unlocked(self, request):
        user = request.user
        title_unlock = TaggTitleFontColorUnlock.objects.filter(user=user).first()
        if not title_unlock:
            # creating title_unlock since it doesn't exist for the user
            title_unlock = TaggTitleFontColorUnlock.objects.create(user=user)
        data = {
            "tagg_title_font_color_unlocked": title_unlock.tagg_title_font_color_unlocked
        }
        return Response(data, status=200)

    @action(detail=False, methods=["post"])
    def unlock(self, request):
        user = request.user
        title_unlock = TaggTitleFontColorUnlock.objects.filter(user=user).first()
        if not title_unlock:
            # creating title_unlock since it doesn't exist for the user
            title_unlock = TaggTitleFontColorUnlock.objects.create(user=user)
            data = {
                "tagg_title_font_color_unlocked": title_unlock.tagg_title_font_color_unlocked
            }
            return Response(data, status=200)

        title_unlock.tagg_title_font_color_unlocked = True
        title_unlock.save()

        game_profile = GameProfile.objects.filter(tagg_user=user).first()
        if not game_profile:
            return Response(data="GameProfile does not exist", status=404)

        if game_profile.tagg_score < 30:
            self.logger.error("Not sufficient tagg score")
            return Response(data="Not sufficient tagg score", status=400)

        # deduct 30 coins from tagg score
        game_profile.tagg_score -= 30
        game_profile.save()
        # tma-2031
        game_profile.tier = determine_gamification_tier(game_profile.tagg_score)
        game_profile.save()

        data = {
            "tagg_title_font_color_unlocked": title_unlock.tagg_title_font_color_unlocked,
            "remaining_coins": game_profile.tagg_score,
        }
        return Response(data, status=200)


# tma-1994, Unlocks feature to change thumbnail image of any tagg
class UnlockTaggThumbnailImage(ViewSet):

    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post"]

    @action(detail=False, methods=["get"])
    def is_unlocked(self, request):
        user = request.user
        widget_count = False
        if Widget.objects.filter(owner=user).count() >= 4:
            widget_count = True
        thumbanil_unlock = TaggThumbnailImageUnlock.objects.filter(user=user).first()
        if not thumbanil_unlock:
            # creating thumbnail image since it doesn't exist for the user
            thumbanil_unlock = TaggThumbnailImageUnlock.objects.create(user=user)
        data = {
            "tagg_thumb_image_unlocked": thumbanil_unlock.tagg_thumb_image_unlocked,
            "is_award_shown": thumbanil_unlock.is_award_shown,
            "widget_count": widget_count
        }
        return Response(data, status=200)

    @action(detail=False, methods=["post"])
    def unlock(self, request):
        user = request.user
        # unlock feature to add thumnail image to tagg if Widget count for a user reaches 4
        if Widget.objects.filter(owner=user).count() >= 4:
            image_unlock = TaggThumbnailImageUnlock.objects.filter(
                user=request.user
            ).first()
            if not image_unlock:
                image_unlock = TaggThumbnailImageUnlock.objects.create(
                    user=request.user
                )
            image_unlock.tagg_thumb_image_unlocked = True
            image_unlock.save()
            data = {
                "tagg_thumb_image_unlocked": image_unlock.tagg_thumb_image_unlocked,
                "is_award_shown": image_unlock.is_award_shown
            }
            return Response(data, status=200)
        else:
            return Response(data="Not sufficient tagg count", status=400)

    @action(detail=False, methods=["post"])
    def award_shown(self, request):
        user = request.user
        data = {"is_award_shown": False}
        unlockObj = TaggThumbnailImageUnlock.objects.filter(user=user).first()
        if not unlockObj:
            return Response(
                "TaggThumbnailImageUnlock object for user doesn'\t exist", status=200
            )
        unlockObj.is_award_shown = True
        unlockObj.save()
        data["is_award_shown"] = unlockObj.is_award_shown
        return Response(data, status=200)

    @action(detail=False, methods=["get"])
    def is_award_shown(self, request):
        user = request.user
        data = {"is_award_shown": False}
        unlockObj = TaggThumbnailImageUnlock.objects.filter(user=user).first()
        if not unlockObj:
            return Response(data, status=200)
        data["is_award_shown"] = unlockObj.is_award_shown
        return Response(data, status=200)
