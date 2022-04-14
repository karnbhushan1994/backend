from rest_framework import routers

from .api import UserProfileInfoViewSet

router = routers.DefaultRouter()
router.register("api/user-profile-info", UserProfileInfoViewSet, "user-profile-info")
urlpatterns = router.urls
