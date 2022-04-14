from rest_framework import routers

from .api import (
    InitialTwitterRequestViewSet,
    LinkFBViewSet,
    LinkInstagramViewSet,
    CallbackRedirectViewset,
    LinkTwitterViewSet,
    LinkedSocialsViewSet,
    LinkSnapchatViewSet,
    LinkTikTokViewSet,
)


router = routers.DefaultRouter()
router.register("api/link-fb", LinkFBViewSet, "link-fb")
router.register("api/link-ig", LinkInstagramViewSet, "link-ig")
router.register("api/link-twitter", LinkTwitterViewSet, "link-twitter")
router.register(
    "api/link-twitter-request", InitialTwitterRequestViewSet, "link-twitter-request"
)
router.register("api/callback", CallbackRedirectViewset, "callback")
router.register("api/linked-socials", LinkedSocialsViewSet, "linked-socials")
router.register("api/link-sc", LinkSnapchatViewSet, "link-sc")
router.register("api/link-tt", LinkTikTokViewSet, "link-tt")
urlpatterns = router.urls
