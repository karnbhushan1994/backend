from rest_framework import routers

from .api import ProfileViewSet, TaggScoreViewSet

router = routers.DefaultRouter()
router.register("api/profile", ProfileViewSet, "profile")
router.register("api/taggscore", TaggScoreViewSet, "taggscore")
urlpatterns = router.urls
