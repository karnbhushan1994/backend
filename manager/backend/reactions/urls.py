from rest_framework import routers
from fcm_django.api.rest_framework import FCMDeviceAuthorizedViewSet
from .api import CommentReactionsListViewSet, CommentThreadsReactionsListViewSet

# , MomentReactionsListViewSet,

router = routers.DefaultRouter()
router.register("api/reaction-comment", CommentReactionsListViewSet, "reaction-comment")
router.register(
    "api/reaction-reply", CommentThreadsReactionsListViewSet, "reaction-reply"
)
# router.register("api/reaction-moment",
#                 MomentReactionsListViewSet, "reaction-moment")

urlpatterns = router.urls
