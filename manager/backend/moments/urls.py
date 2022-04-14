from rest_framework import routers

from .api import (
    MomentDiscoverViewSet,
    MomentsViewSet,
    MomentThumbnailViewSet,
    MomentListViewSet,
    ProfileRewardViewSet,
    MomentCreateViewSet,
    DailyMomentViewSet,
    PermissionViewSet,
    InvitedViewSet,
    InviteUsersViewSet,
    SkinPermissionViewSet
)

from .shares.api import MomentShareViewSet
from .views.api import MomentViewsViewSet, MomentCoinDisplayViewSet

router = routers.DefaultRouter()
router.register("api/moments", MomentsViewSet, "moments")
router.register("api/discover-moments", MomentDiscoverViewSet, "discover-moments")
router.register("api/skin-permission", SkinPermissionViewSet, "skin-permissions")
router.register("api/moment-thumbnail", MomentThumbnailViewSet, "moment-thumbnail")
router.register("api/permission", PermissionViewSet, "moment-thumbnail")
router.register("api/momentCreate", MomentCreateViewSet, "moment-create")
router.register("api/invite-user", InviteUsersViewSet, "invite-user")
router.register("api/rewardCheck", ProfileRewardViewSet, "rewardadmin")
router.register("api/momentList", MomentListViewSet, "moment")
router.register("api/moment-view", MomentViewsViewSet, "moment-view")
router.register("api/moment-share", MomentShareViewSet, "moment-share")
router.register("api/moment-daily",DailyMomentViewSet, "daily-moments")
router.register("api/moment-coin-display", MomentCoinDisplayViewSet, "moment-coin-display")
router.register("api/invite-users",InvitedViewSet , "users-invite")
# http://localhost:8000/api/moment-view-count/visit/
# POST - data form body {moment_id: ""}, header {Authorization: "Token ****"}

# http://localhost:8000/api/moment-view-count/visitor_count/
# GET - query params {filter_type: "PAST_7_DAYS", moment_id: ""}, header {Authorization: "Token ****"}
# Response - JSON("moment_views": x)

# http://localhost:8000/api/top-moment/top_moment/
# GET - query params {user_id: ""}
# Response - JSON("shareCount": "", "commentCount": "", "viewCount": "")

urlpatterns = router.urls
