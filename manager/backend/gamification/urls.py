from rest_framework import routers

from .api import GameProfileViewSet, FeatureViewSet, UserFeatureViewSet

router = routers.DefaultRouter()
router.register("api/game_profile", GameProfileViewSet, "game_profile")
router.register("api/feature", FeatureViewSet, "feature")
router.register("api/user_feature", UserFeatureViewSet, "user_feature")

urlpatterns = router.urls
