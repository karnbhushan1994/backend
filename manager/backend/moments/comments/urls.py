from rest_framework import routers

from .api import (
    CommentThreadsViewSet,
    MomentCommentsViewSet,
)

router = routers.DefaultRouter()
router.register("api/comments", MomentCommentsViewSet, "comments")
router.register("api/reply", CommentThreadsViewSet, "reply")
urlpatterns = router.urls
