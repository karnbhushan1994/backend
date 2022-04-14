from rest_framework import routers

from .api import (
    SocialMediaWidgetViewSet,
    ApplicationLinkWidgetViewSet,
    GenericLinkWidgetViewSet,
    VideoLinkWidgetViewSet,
    WidgetViewSet,
    PresignedURLViewset,
    RewardsAdd,
    UnlockBackground,
    UnlockTaggTitleFontColor,
    UnlockTaggThumbnailImage,
)

router = routers.DefaultRouter()
router.register("api/widget", WidgetViewSet, "widget")
router.register("api/video_link_widget", VideoLinkWidgetViewSet, "video_link_widget")
router.register(
    "api/application_link_widget",
    ApplicationLinkWidgetViewSet,
    "application_link_widget",
)
router.register(
    "api/generic_link_widget", GenericLinkWidgetViewSet, "generic_link_widget"
)
router.register(
    "api/rewards-add", RewardsAdd, "rewards"
)

router.register(
    "api/social_media_widget", SocialMediaWidgetViewSet, "social_media_widget"
)

router.register("api/presigned-url-thumbnail", PresignedURLViewset, "presigned-url")
router.register("api/unlock_background", UnlockBackground, "unlock_background")
router.register(
    "api/unlock_tagg_title_font", UnlockTaggTitleFontColor, "unlock_background"
)
router.register(
    "api/unlock_tagg_thumbnail", UnlockTaggThumbnailImage, "unlock_thumbnail"
)
urlpatterns = router.urls
